#!/usr/bin/python3
# This file was automatically generated from drawio2cbd with the command:
#   __main__.py ..\diagrams\CBD_equation_1.drawio -F CBD -e CBD_equation_1 -d ..\generated -t 20 -E delta=0.1

from CBD.model import *
from CBD.library import *

DELTA_T = 0.1

class CBD_equation_1(CBD):
    def __init__(self, block_name):
        super().__init__(block_name, input_ports=[], output_ports=['y', 't'])

        # Create the Blocks
        self.addBlock(AdderBlock("sum2", numberOfInputs=(2)))
        self.addBlock(AdderBlock("sum1", numberOfInputs=(2)))
        self.addBlock(ConstantBlock("c53", value=(5/3)))
        self.addBlock(DelayBlock("d"))
        self.addBlock(ConstantBlock("c17", value=(17)))
        self.addBlock(GenericBlock("sin1", block_operator=("sin")))
        self.addBlock(NegatorBlock("neg1"))
        self.addBlock(ProductBlock("prod1", numberOfInputs=(2)))
        self.addBlock(ConstantBlock("c01", value=(0.1)))
        self.addBlock(TimeBlock("time"))

        # Create the Connections
        self.addConnection("sum2", "y", output_port_name='OUT1')
        self.addConnection("sum1", "sum2", output_port_name='OUT1', input_port_name='IN1')
        self.addConnection("c53", "sum1", output_port_name='OUT1', input_port_name='IN1')
        self.addConnection("d", "sum1", output_port_name='OUT1', input_port_name='IN2')
        self.addConnection("c17", "d", output_port_name='OUT1', input_port_name='IC')
        self.addConnection("sin1", "d", output_port_name='OUT1', input_port_name='IN1')
        self.addConnection("neg1", "sum2", output_port_name='OUT1', input_port_name='IN2')
        self.addConnection("prod1", "neg1", output_port_name='OUT1', input_port_name='IN1')
        self.addConnection("c01", "prod1", output_port_name='OUT1', input_port_name='IN2')
        self.addConnection("time", "sin1", output_port_name='OUT1', input_port_name='IN1')
        self.addConnection("time", "prod1", output_port_name='OUT1', input_port_name='IN1')
        self.addConnection("time", "t", output_port_name='OUT1')


