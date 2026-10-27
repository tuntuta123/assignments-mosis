#!/usr/bin/python3
# This file was automatically generated from drawio2cbd with the command:
#   __main__.py ../diagrams/Integrator.drawio -F CBD -e Integrator -d ../generated

from CBD.model import *
from CBD.library import *


class Integrator(CBD):
    def __init__(self, block_name):
        super().__init__(block_name, input_ports=['IC', 'IN1', 'DT'], output_ports=['OUT1'])

        # Create the Blocks
        self.addBlock(ProductBlock("product", numberOfInputs=(2)))
        self.addBlock(AdderBlock("adder", numberOfInputs=(2)))
        self.addBlock(DelayBlock("delay"))

        # Create the Connections
        self.addConnection("IN1", "product", input_port_name='IN1')
        self.addConnection("DT", "product", input_port_name='IN2')
        self.addConnection("product", "adder", output_port_name='OUT1', input_port_name='IN1')
        self.addConnection("adder", "delay", output_port_name='OUT1', input_port_name='IN1')
        self.addConnection("IC", "delay", input_port_name='IC')
        self.addConnection("delay", "adder", output_port_name='OUT1', input_port_name='IN2')
        self.addConnection("delay", "OUT1", output_port_name='OUT1')


