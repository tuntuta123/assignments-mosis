from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from CBD.model import CBD
from CBD.library import *
from CBD.library import FMUBlock
from CBD.fmi2 import FMU2CoSimulation
from CBD.optimized_simulator import Simulator

HERE = Path(__file__).resolve().parent

# same experiment as the modelica assignment
KP = 800_000
KI = 10
KD = 10_000
SETPOINT = 0.5
DELTA_T = 0.002
STOP_TIME = 40

FMU_PATH = HERE / "PlantFMU.fmu"

# PID force at t = 0 in the modelica ControlledCar run (steady state,
# pIDController.control_output(0)). the FMU starts from this force so both
# simulations start from the same equilibrium
# result (run with -override=Kp=800000,Ki=10,Kd=10000)
INITIAL_FORCE = 356.32086714746276

class PlantFMUBlock(FMUBlock):
    # the modelica ControlledCar starts in steady state with the PID already pushing a force of 356.32 N
    # the exported plant alone starts with u = 0, so it settles at a different height. setting the input before initialization
    # makes the FMU start from the same steady state as the modelica model.
    def __init__(self, block_name, fmu_path, initial_input, **kwargs):
        super().__init__(block_name, fmu_path=fmu_path, **kwargs)
        self._initial_input = initial_input

    def _open(self):
        if self._fmu is not None:
            return
        self._fmu = FMU2CoSimulation(self._fmu_path)
        self._input_reference = self._fmu.value_references[self._input_name]
        self._output_reference = self._fmu.value_references[self._output_name]
        self._fmu.instantiate()
        self._fmu.set_real(self._input_reference, self._initial_input)
        self._fmu.setup()

    def close(self):
        # fmi2FreeInstance crashes the python process for the CVODE export,
        # so only terminate; the memory is released when the process exits
        if self._fmu is None:
            return
        self._fmu.terminate()
        self._fmu = None


class PIDController(CBD):
    # u = Kp * e + Ki * integral(e) + Kd * de/dt, with e = setpoint - height
    def __init__(self, block_name, kp, ki, kd):
        super().__init__(block_name, input_ports=["setpoint", "height"], output_ports=["u"])

        self.addBlock(NegatorBlock("neg_height"))
        self.addBlock(AdderBlock("error", numberOfInputs=2))

        self.addBlock(ConstantBlock("kp", value=kp))
        self.addBlock(ConstantBlock("ki", value=ki))
        self.addBlock(ConstantBlock("kd", value=kd))
        self.addBlock(ConstantBlock("zero", value=0))
        self.addBlock(DeltaTBlock("deltaT"))

        self.addBlock(ProductBlock("p", numberOfInputs=2))
        self.addBlock(IntegratorBlock("integrator"))
        self.addBlock(ProductBlock("i", numberOfInputs=2))
        self.addBlock(DerivatorBlock("derivator"))
        self.addBlock(ProductBlock("d", numberOfInputs=2))
        self.addBlock(AdderBlock("sum", numberOfInputs=3))

        # e = setpoint - height
        self.addConnection("height", "neg_height", input_port_name="IN1")
        self.addConnection("setpoint", "error", input_port_name="IN1")
        self.addConnection("neg_height", "error", input_port_name="IN2")

        # P
        self.addConnection("error", "p", input_port_name="IN1")
        self.addConnection("kp", "p", input_port_name="IN2")

        # I (starts at 0, like y_start = 0 in modelica)
        self.addConnection("error", "integrator", input_port_name="IN1")
        self.addConnection("zero", "integrator", input_port_name="IC")
        self.addConnection("deltaT", "integrator", input_port_name="DT")
        self.addConnection("integrator", "i", input_port_name="IN1")
        self.addConnection("ki", "i", input_port_name="IN2")

        # D: backward difference (e[i] - e[i-1]) / dt from the CBD library
        # IC = 0 makes the output 0 at t = 0, like SteadyState in modelica
        self.addConnection("error", "derivator", input_port_name="IN1")
        self.addConnection("zero", "derivator", input_port_name="IC")
        self.addConnection("deltaT", "derivator", input_port_name="DT")
        self.addConnection("derivator", "d", input_port_name="IN1")
        self.addConnection("kd", "d", input_port_name="IN2")

        # sum
        self.addConnection("p", "sum", input_port_name="IN1")
        self.addConnection("i", "sum", input_port_name="IN2")
        self.addConnection("d", "sum", input_port_name="IN3")
        self.addConnection("sum", "u")


class ControlledCarCoSim(CBD):
    # SP -> PID -> plant FMU, chassis height fed back to the PID
    def __init__(self, block_name, fmu_path, kp, ki, kd, setpoint, initial_force=0.0):
        super().__init__(block_name, input_ports=[], output_ports=["height", "force"])

        self.addBlock(ConstantBlock("SP", value=setpoint))
        self.addBlock(PIDController("pid", kp, ki, kd))
        self.addBlock(PlantFMUBlock("plant", fmu_path, initial_force, input_name="u", output_name="y"))

        self.addConnection("SP", "pid", input_port_name="setpoint")
        self.addConnection("plant", "pid", input_port_name="height")
        self.addConnection("pid", "plant", output_port_name="u", input_port_name="IN1")

        self.addConnection("plant", "height")
        self.addConnection("pid", "force", output_port_name="u")


def run_cbd():
    model = ControlledCarCoSim("car", FMU_PATH, KP, KI, KD, SETPOINT, INITIAL_FORCE)

    sim = Simulator(model)
    sim.setDeltaT(DELTA_T)
    sim.run(STOP_TIME)

    plant = model.getBlockByName("plant")
    height_signal = plant.getSignalHistory()
    force_signal = model.getBlockByName("pid").getBlockByName("sum").getSignalHistory()
    plant.close()

    time = np.array([s.time for s in height_signal])
    height = np.array([s.value for s in height_signal])
    force = np.array([s.value for s in force_signal])

    return time, height, force


def plot(time, height, force):
    fig, (top, bottom) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)

    top.plot(time, height, label="chassis height (CBD PID + plant FMU)")
    top.axhline(SETPOINT, color="grey", linestyle=":", label="setpoint 0.5 m")
    top.set_ylabel("chassis height [m]")
    top.set_title(f"Kp={KP:,}, Ki={KI}, Kd={KD:,}, $\\Delta t$={DELTA_T} s")
    top.legend()
    top.grid(True)

    bottom.plot(time, force)
    bottom.set_ylabel("PID force [N]")
    bottom.set_xlabel("time [s]")
    bottom.grid(True)

    fig.tight_layout()

    output = HERE / "fmu_results" / "cosimulation.png"
    fig.savefig(output, dpi=150)

    return output


if __name__ == "__main__":
    (HERE / "fmu_results").mkdir(exist_ok=True)

    time, height, force = run_cbd()
    output = plot(time, height, force)

    print(f"CBD steps: {len(time)}, last t = {time[-1]:.3f} s")
    print(f"Plot saved to {output}")
