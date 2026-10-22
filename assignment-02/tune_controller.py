import os
import time
import numpy as np
from scipy import io

def readMat(matFileName):
    dataMat = io.loadmat(matFileName)
    info = dataMat["dataInfo"]
    is_transposed = str(np.asarray(dataMat["Aclass"]).reshape(-1)[3]) == "binTrans"

    if is_transposed:
        names = [""] * info.shape[1]
        data = [None] * len(names)
        encoded_names = dataMat["name"].reshape(-1)
        for i in range(len(names)):
            for row in encoded_names:
                if i < len(row) and row[i] != "\x00":
                    names[i] += row[i]

        for i in range(len(names)):
            variable_type = info[0][i]
            variable_index = info[1][i]
            source = dataMat["data_2"] if variable_type in (0, 2) else dataMat["data_1"]
            value = source[abs(variable_index) - 1]
            if variable_type == 1:
                value = value[0]
            if variable_index < 0:
                value = -value
            data[i] = value
    else:
        names = [str(name).rstrip("\x00") for name in dataMat["name"].reshape(-1)]
        data = [None] * len(names)
        for i in range(len(names)):
            variable_type = info[i][0]
            variable_index = info[i][1]
            source = dataMat["data_2"] if variable_type in (0, 2) else dataMat["data_1"]
            value = source[abs(variable_index) - 1]
            if variable_type == 1:
                value = value[0]
            if variable_index < 0:
                value = -value
            data[i] = value

    return [names, data]

def run_simulation(
    build_dir, exe_name, result_file, kp, ki, kd, cost_limit, **extra_overrides
):
    parameters = {
        "Kp": kp,
        "Ki": ki,
        "Kd": kd,
        "costLimit": cost_limit,
        **extra_overrides,
    }
    override = ",".join(f"{name}={value}" for name, value in parameters.items())
    command = (
        f'"{exe_name}" -override={override} -r="{result_file}"'
    )
    os.system(f'cd /d "{build_dir}" && {command}')

    result_path = os.path.join(build_dir, result_file)
    names, data = readMat(result_path)
    return dict(zip(names, data))

def run_tuning():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(script_dir, "SuspensionSystem.ControlledCar")
    exe_name = "ControlledCar.bat"
    result_file = "ControlledCar_res.mat"

    kp_range = range(100_000, 1_000_000 + 1, 100_000)
    ki_range = (0, 1, 10, 100, 1_000)
    kd_range = (0, 500, 1_000, 2_000, 5_000, 10_000, 20_000, 50_000)
    simulation_count = len(kp_range) * len(ki_range) * len(kd_range)

    head_early_terms = 0
    height_early_terms = 0
    cost_early_terms = 0
    best_cost = 1e30
    best_parameters = None
    start_time = time.perf_counter()

    for kp in kp_range:
        for ki in ki_range:
            for kd in kd_range:
                simulation = run_simulation(
                    build_dir, exe_name, result_file, kp, ki, kd, best_cost
                )
                final_cost = float(np.asarray(simulation["cost"])[-1])
                head_exceeded = bool(
                    np.asarray(simulation["headLimitExceeded"])[-1]
                )
                height_exceeded = bool(
                    np.asarray(simulation["heightLimitExceeded"])[-1]
                )
                cost_exceeded = bool(
                    np.asarray(simulation["costLimitExceeded"])[-1]
                )

                if head_exceeded:
                    head_early_terms += 1
                if height_exceeded:
                    height_early_terms += 1
                if cost_exceeded:
                    cost_early_terms += 1
                if head_exceeded or height_exceeded:
                    continue

                if cost_exceeded:
                    continue

                if final_cost < best_cost:
                    best_cost = final_cost
                    best_parameters = (kp, ki, kd)

    elapsed_seconds = time.perf_counter() - start_time
    if best_parameters is None:
        print("No acceptable controller found.")
    else:
        kp, ki, kd = best_parameters
        print(f"Best controller: Kp={kp:,}, Ki={ki:,}, Kd={kd:,}")
        print(f"Cost: {best_cost:.6f}")
    print(
        f"Early terminations: head={head_early_terms}, "
        f"height={height_early_terms}, cost={cost_early_terms}"
    )
    print(f"Tuning time: {elapsed_seconds:.2f} s ({simulation_count} simulations)")

    # uncapped_start_time = time.perf_counter()
    # for kp in kp_range:
    #     for ki in ki_range:
    #         for kd in kd_range:
    #             run_simulation(
    #                 build_dir,
    #                 exe_name,
    #                 result_file,
    #                 kp,
    #                 ki,
    #                 kd,
    #                 1e30,
    #                 headAccelerationLimit=1e30,
    #                 minHeight=-1e30,
    #                 maxHeight=1e30,
    #             )
    # uncapped_elapsed_seconds = time.perf_counter() - uncapped_start_time
    # seconds_saved = uncapped_elapsed_seconds - elapsed_seconds
    # print(f"Unrestricted tuning time: {uncapped_elapsed_seconds:.2f} s")
    # print(f"Time saved by early termination: {seconds_saved:.2f} s")
    # print(
    #     f"Percentage saved: "
    #     f"{100 * seconds_saved / uncapped_elapsed_seconds:.1f}%"
    # )

if __name__ == "__main__":
    run_tuning()
