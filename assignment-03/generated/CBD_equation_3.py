#!/usr/bin/python3
# This file was automatically generated from drawio2cbd with the command:
#   __main__.py ..\diagrams\CBD_equation_3.drawio -F CBD -e CBD_equation_3 -d ..\generated -t 20 -E delta=0.1

from CBD.model import *
from CBD.library import *

DELTA_T = 0.1

class CBD_equation_3(CBD):
    def __init__(self, block_name):
        super().__init__(block_name, input_ports=[], output_ports=['y'])

        # Create the Blocks
        self.addBlock(ConstantBlock("c5", value=(5)))
        self.addBlock(AdderBlock("sum1", numberOfInputs=(2)))
        self.addBlock(NegatorBlock("neg1"))
        self.addBlock(ConstantBlock("c2", value=(2)))
        self.addBlock(ProductBlock("prod1", numberOfInputs=(2)))
        self.addBlock(InverterBlock("inv1"))

        # Create the Connections
        self.addConnection("c5", "sum1", output_port_name='OUT1', input_port_name='IN1')
        self.addConnection("neg1", "sum1", output_port_name='OUT1', input_port_name='IN2')
        self.addConnection("neg1", "y", output_port_name='OUT1')
        self.addConnection("sum1", "prod1", output_port_name='OUT1', input_port_name='IN1')
        self.addConnection("c2", "prod1", output_port_name='OUT1', input_port_name='IN2')
        self.addConnection("prod1", "inv1", output_port_name='OUT1', input_port_name='IN1')
        self.addConnection("inv1", "neg1", output_port_name='OUT1', input_port_name='IN1')


