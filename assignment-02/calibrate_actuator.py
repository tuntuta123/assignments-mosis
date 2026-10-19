import os
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
    # Setup working folders relative to where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(script_dir, "SuspensionSystem.ActuatorTestBench")
    csv_path = os.path.join(script_dir, "calibration_data.csv")
    exe_name = "ActuatorTestBench.bat"

    print(f"Loading assignment hardware dataset from: {csv_path}")
    raw_csv = np.genfromtxt(csv_path, delimiter=',', skip_header=1)
    t_exp = raw_csv[:, 1]
    f_exp = raw_csv[:, 2]

    # Setup the optimization loop ranges
    c2_range = np.arange(0, 400000 + 10000, 10000)  # 41 points
    d2_range = np.arange(0, 15000 + 250, 250)  # 61 points

    best_sse = float('inf')
    best_c2, best_d2 = None, None

    # Step into the project directory to isolate simulation execution
    os.chdir(build_dir)
    print(f"Starting 2,501 loops inside directory: {build_dir}...\nRunning...")

    for c2 in c2_range:
        for d2 in d2_range:
            simulation_command = f"{exe_name} -override=c2={c2},d2={d2} -r=ActuatorTestBench_res.mat"

            # Simulate the model via the system shell
            os.system(simulation_command)

            # Safety check: Verify the execution successfully created the file
            if not os.path.exists('ActuatorTestBench_res.mat'):
                print(f"\n--- WINDOWS EXECUTION ERROR ---")
                print(f"The terminal refused to launch: {simulation_command}")
                print(f"Current working path directory content is: {os.listdir('.')}")
                raise FileNotFoundError("Simulation engine binary did not generate output.")

            # Obtain the variable values by reading the MAT-file
            [names, data] = readMat('ActuatorTestBench_res.mat')

            # Locate structural indices using clean list lookups
            t_index = names.index('time')
            f_index = names.index('actuator.f')

            t_sim = data[t_index]
            f_sim = data[f_index]

            # Time-align curves and compute objective error minimization tracking cost
            f_sim_interp = np.interp(t_exp, t_sim, f_sim)
            sse = np.sum((f_exp - f_sim_interp) ** 2)

            if sse < best_sse:
                best_sse = sse
                best_c2 = c2
                best_d2 = d2

    print(f"Optimal Non-Linear Stiffness (c2):  {best_c2:,} N/m^3")
    print(f"Optimal Non-Linear Damping   (d2):  {best_d2:,} N.s^3/m^3")
    print(f"Minimum Fit Error Residual  (SSE): {best_sse:.4e}")

if __name__ == "__main__":
    run_calibration()
