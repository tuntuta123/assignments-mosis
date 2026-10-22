import os
import subprocess

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import io

def readMat(matFileName):
    dataMat = io.loadmat(matFileName)
    names = [''] * len(dataMat['name'][0])
    data = [None] * len(names)
    # Check if the matrix of metadatas are transposed.
    if dataMat['Aclass'][3] == 'binTrans':
        # If the matrix of  matadata needs to be transposed, the names nead to be read from each string
        for x in range(len(dataMat['name'])):
            for i in range(len(dataMat['name'][x])):
                if dataMat['name'][x][i] != '\x00':
                    names[i] = names[i] + dataMat['name'][x][i]
        # If the matrix of metadata needs to be transposed, the index of variable trace needs to be read in a transposed fashion
        for i in range(len(names)):
            # If it is a variable, read the whole array
            if (dataMat['dataInfo'][0][i] == 0) or (dataMat['dataInfo'][0][i] == 2):
                data[i] = dataMat['data_2'][dataMat['dataInfo'][1][i] - 1]
            # If it is a parameter, read only the first value
            elif dataMat['dataInfo'][0][i] == 1:
                data[i] = dataMat['data_1'][dataMat['dataInfo'][1][i] - 1][0]
    else:
        # If the matrix of metadata need not be transposed, the names can be read directly as individual strings
        names = dataMat['name']
        # If the matrix of metadata need not be transposed, the index of variable trace needs to be read directly
        for i in range(len(names)):
            # If it is a variable, read the whole array
            if (dataMat['dataInfo'][i][0] == 0) or (dataMat['dataInfo'][i][0] == 2):
                data[i] = dataMat['data_2'][dataMat['dataInfo'][i][1] - 1]
            # If it is a parameter, read only the first value
            elif dataMat['dataInfo'][i][0] == 1:
                data[i] = dataMat['data_1'][dataMat['dataInfo'][i][1] - 1][0]
    # Return the names of variables, and their corresponding values
    return [names, data]


# Calibration (Windows)
def run_calibration():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(script_dir, "SuspensionSystem.ActuatorTestBench")
    csv_path = os.path.join(script_dir, "calibration_data.csv")
    exe_name = "ActuatorTestBench.bat"
    result_file = "ActuatorTestBench_calibration_res.mat"

    print(f"Loading assignment hardware dataset from: {csv_path}")
    raw_csv = np.genfromtxt(csv_path, delimiter=',', skip_header=1)
    t_exp = raw_csv[:, 1]
    f_exp = raw_csv[:, 2]

    c2_range = np.arange(0, 400000 + 10000, 10000)  # 41 points
    d2_range = np.arange(0, 15000 + 250, 250)  # 61 points

    best_sse = float('inf')
    best_c2, best_d2 = None, None
    sse_grid = np.empty((len(c2_range), len(d2_range)))

    print(f"Starting {sse_grid.size:,} simulations in {build_dir}...")

    for c2_index, c2 in enumerate(c2_range):
        for d2_index, d2 in enumerate(d2_range):
            simulation_command = (
                f"{exe_name} -override=c2={c2},d2={d2} "
                f"-r={result_file}"
            )

            subprocess.run(
                simulation_command,
                cwd=build_dir,
                shell=True,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
            )

            result_path = os.path.join(build_dir, result_file)
            if not os.path.exists(result_path):
                raise FileNotFoundError(
                    f"Simulation did not generate output: {result_path}"
                )

            names, data = readMat(result_path)

            t_index = names.index('time')
            f_index = names.index('actuator.f')
            t_sim = data[t_index]
            f_sim = data[f_index]

            f_sim_interp = np.interp(t_exp, t_sim, f_sim)
            sse = np.sum((f_exp - f_sim_interp) ** 2)
            sse_grid[c2_index, d2_index] = sse

            if sse < best_sse:
                best_sse = sse
                best_c2 = c2
                best_d2 = d2

    best_command = (
        f"{exe_name} -override=c2={best_c2},d2={best_d2} "
        f"-r={result_file}"
    )
    subprocess.run(
        best_command,
        cwd=build_dir,
        shell=True,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    result_path = os.path.join(build_dir, result_file)
    names, data = readMat(result_path)
    os.remove(result_path)
    t_sim = data[names.index('time')]
    f_sim = data[names.index('actuator.f')]
    f_sim_interp = np.interp(t_exp, t_sim, f_sim)
    residuals = f_exp - f_sim_interp

    fit_plot_path = os.path.join(script_dir, "calibration_fit.png")
    fig, (fit_axis, residual_axis) = plt.subplots(
        2, 1, figsize=(10, 7), sharex=True,
        gridspec_kw={"height_ratios": [3, 1]},
    )
    fit_axis.scatter(
        t_exp, f_exp, label="Measured data", color="dimgray",
        s=12, alpha=0.75, zorder=2,
    )
    fit_axis.plot(
        t_sim, f_sim, label="Calibrated simulation",
        color="royalblue", linewidth=1.8,
    )
    fit_axis.set_ylabel("Actuator force (N)")
    fit_axis.set_title(
        f"Actuator calibration: c2={best_c2:,} N/m^3, d2={best_d2:,} N.s^3/m^3"
    )
    fit_axis.legend()
    fit_axis.grid(True, linestyle=":", alpha=0.6)
    residual_axis.plot(t_exp, residuals, color="darkorange", linewidth=1)
    residual_axis.axhline(0, color="black", linewidth=0.8)
    residual_axis.set_xlabel("Time (s)")
    residual_axis.set_ylabel("Residual (N)")
    residual_axis.grid(True, linestyle=":", alpha=0.6)
    fig.tight_layout()
    fig.savefig(fit_plot_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    heatmap_path = os.path.join(script_dir, "calibration_sse_heatmap.png")
    fig, axis = plt.subplots(figsize=(9, 6))
    image = axis.imshow(
        sse_grid,
        origin="lower",
        aspect="auto",
        extent=(
            d2_range[0] - 125,
            d2_range[-1] + 125,
            c2_range[0] - 5000,
            c2_range[-1] + 5000,
        ),
        cmap="viridis",
    )
    axis.scatter(best_d2, best_c2, color="red", marker="x", s=70, label="Minimum SSE")
    axis.set_xlabel("Nonlinear damping coefficient d2 (N.s^3/m^3)")
    axis.set_ylabel("Nonlinear stiffness coefficient c2 (N/m^3)")
    axis.set_title("Actuator calibration SSE over parameter grid")
    axis.legend()
    fig.colorbar(image, ax=axis, label="SSE (N^2)")
    fig.tight_layout()
    fig.savefig(heatmap_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    report_path = os.path.join(script_dir, "actuator_calibration_report.md")
    with open(report_path, "w", encoding="utf-8", newline="\n") as report:
        report.write(
            "# Actuator calibration report\n\n"
            "## Results\n\n"
            "| Quantity | Calibrated value |\n"
            "| --- | ---: |\n"
            f"| Nonlinear stiffness, `c2` | {best_c2:,} N/m^3 |\n"
            f"| Nonlinear damping, `d2` | {best_d2:,} N.s^3/m^3 |\n"
            f"| Sum of squared errors (SSE) | {best_sse:.8e} N^2 |\n"
            f"| Measured samples | {len(t_exp):,} |\n"
            f"| Parameter combinations evaluated | {sse_grid.size:,} |\n\n"
            "## Method\n\n"
            "The actuator model was simulated for each pair on a grid of "
            "`c2 = 0..400000 N/m^3` in steps of `10000 N/m^3` and "
            "`d2 = 0..15000 N.s^3/m^3` in steps of `250 N.s^3/m^3`. "
            "The simulated force was linearly interpolated at the measured "
            "timestamps. The reported objective is "
            "`SSE = sum((measured force - interpolated simulated force)^2)`; "
            "the minimum over the evaluated grid is reported.\n\n"
            "## Simulation versus measured data\n\n"
            "![Measured actuator force and calibrated simulation, with residuals]"
            "(calibration_fit.png)\n\n"
            "## SSE across the parameter grid\n\n"
            "![SSE heatmap over nonlinear stiffness and damping]"
            "(calibration_sse_heatmap.png)\n"
        )

    print(f"Optimal Non-Linear Stiffness (c2):  {best_c2:,} N/m^3")
    print(f"Optimal Non-Linear Damping   (d2):  {best_d2:,} N.s^3/m^3")
    print(f"Minimum Fit Error Residual  (SSE): {best_sse:.4e}")
    print(f"Report: {report_path}")
    print(f"Fit plot: {fit_plot_path}")
    print(f"SSE heatmap: {heatmap_path}")

if __name__ == "__main__":
    run_calibration()
