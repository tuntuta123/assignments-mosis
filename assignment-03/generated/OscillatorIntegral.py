#!/usr/bin/python3
# This file was automatically generated from drawio2cbd with the command:
#   __main__.py ../diagrams/OscillatorIntegral.drawio -F CBD -e OscillatorIntegral -d ../generated

from CBD.model import *
from CBD.library import *


class OscillatorIntegral(CBD):
    def __init__(self, block_name):
        super().__init__(block_name, input_ports=[], output_ports=['X', 'V'])

        # Create the Blocks
        self.addBlock(IntegratorBlock("IntegratorX"))
        self.addBlock(IntegratorBlock("IntegratorV"))
        self.addBlock(NegatorBlock("negator"))
        self.addBlock(DeltaTBlock("deltaT"))
        self.addBlock(ConstantBlock("constant0", value=(0)))
        self.addBlock(ConstantBlock("constant1", value=(1)))

        # Create the Connections
        self.addConnection("IntegratorV", "negator", output_port_name='OUT1', input_port_name='IN1')
        self.addConnection("IntegratorV", "V", output_port_name='OUT1')
        self.addConnection("negator", "IntegratorX", output_port_name='OUT1', input_port_name='IN1')
        self.addConnection("IntegratorX", "IntegratorV", output_port_name='OUT1', input_port_name='IN1')
        self.addConnection("IntegratorX", "X", output_port_name='OUT1')
        self.addConnection("constant1", "IntegratorV", output_port_name='OUT1', input_port_name='IC')
        self.addConnection("deltaT", "IntegratorV", output_port_name='OUT1', input_port_name='DT')
        self.addConnection("deltaT", "IntegratorX", output_port_name='OUT1', input_port_name='DT')
        self.addConnection("constant0", "IntegratorX", output_port_name='OUT1', input_port_name='IC')


