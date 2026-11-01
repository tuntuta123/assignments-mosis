#!/usr/bin/python3
# This file was automatically generated from drawio2cbd with the command:
#   __main__.py ..\diagrams\CBD_equation_3.drawio -F CBD -e CBD_equation_3 -d ..\generated -t 20 -E delta=0.1
from matplotlib import pyplot as plt

from CBD_equation_3 import *
from CBD.simulator import Simulator

DELTA_T = 0.1

cbd = CBD_equation_3("CBD_equation_3")

# Run the Simulation
sim = Simulator(cbd)
sim.setDeltaT(DELTA_T)
try:
    sim.run(20.0)
except ValueError as e:
    print(e)
    raise SystemExit(0)

t_values = [signal.value for signal in cbd.getSignalHistory("t")]
y_values = [signal.value for signal in cbd.getSignalHistory("y")]

plt.plot(t_values, y_values)
plt.xlabel("t")
plt.ylabel("y")
plt.title("CBD_equation_3 Simulation Results")
plt.grid(True)
plt.savefig("CBD_equation_3.png", dpi=150)
plt.show()