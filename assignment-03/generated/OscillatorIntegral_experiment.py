#!/usr/bin/python3
# This file was automatically generated from drawio2cbd with the command:
#   __main__.py ../diagrams/OscillatorIntegral.drawio -F CBD -e OscillatorIntegral -d ../generated -f

from OscillatorIntegral import *
from CBD.simulator import Simulator


cbd = OscillatorIntegral("OscillatorIntegral")

# Run the Simulation
sim = Simulator(cbd)
sim.run(10)

# TODO: Process Your Simulation Results