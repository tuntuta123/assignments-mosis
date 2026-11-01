#!/usr/bin/python3
# This file was automatically generated from drawio2cbd with the command:
#   __main__.py ..\diagrams\CBD_equation_2.drawio -F CBD -e CBD_equation_2 -d ..\generated -t 20 -E delta=0.1

from CBD.model import *
from CBD.library import *

DELTA_T = 0.1

class CBD_equation_2(CBD):
    def __init__(self, block_name):
        super().__init__(block_name, input_ports=[], output_ports=['t', 'y'])

        # Create the Blocks
        self.addBlock(NegatorBlock("neg_d"))
        self.addBlock(DelayBlock("delay_d"))
        self.addBlock(ConstantBlock("c7", value=(7)))
        self.addBlock(TimeBlock("time"))
        self.addBlock(AdderBlock("sum1", numberOfInputs=(2)))
        self.addBlock(ConstantBlock("c11", value=(11)))
        self.addBlock(AdderBlock("sum2", numberOfInputs=(2)))
        self.addBlock(NegatorBlock("neg_y"))
        self.addBlock(ProductBlock("prod1", numberOfInputs=(2)))

        # Create the Connections
        self.addConnection("delay_d", "neg_d", output_port_name='OUT1', input_port_name='IN1')
        self.addConnection("delay_d", "prod1", output_port_name='OUT1', input_port_name='IN1')
        self.addConnection("neg_d", "delay_d", output_port_name='OUT1', input_port_name='IN1')
        self.addConnection("c7", "delay_d", output_port_name='OUT1', input_port_name='IC')
        self.addConnection("c11", "sum1", output_port_name='OUT1', input_port_name='IN2')
        self.addConnection("time", "sum1", output_port_name='OUT1', input_port_name='IN1')
        self.addConnection("time", "t", output_port_name='OUT1')
        self.addConnection("sum1", "sum2", output_port_name='OUT1', input_port_name='IN1')
        self.addConnection("neg_y", "sum2", output_port_name='OUT1', input_port_name='IN2')
        self.addConnection("neg_y", "y", output_port_name='OUT1')
        self.addConnection("sum2", "prod1", output_port_name='OUT1', input_port_name='IN2')
        self.addConnection("prod1", "neg_y", output_port_name='OUT1', input_port_name='IN1')


