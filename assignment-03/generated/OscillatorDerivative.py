#!/usr/bin/python3
# This file was automatically generated from drawio2cbd with the command:
#   __main__.py ../diagrams/OscillatorDerivative.drawio -F CBD -e OscillatorDerivative -d ../generated

from CBD.model import *
from CBD.library import *


class OscillatorDerivative(CBD):
    def __init__(self, block_name):
        super().__init__(block_name, input_ports=[], output_ports=['X', 'V'])

        # Create the Blocks
        self.addBlock(NegatorBlock("negator"))
        self.addBlock(DerivatorBlock("DerivatorX"))
        self.addBlock(DerivatorBlock("DerivatorV"))
        self.addBlock(ConstantBlock("constant0", value=(0)))
        self.addBlock(ConstantBlock("constant1", value=(1)))
        self.addBlock(DeltaTBlock("deltaT"))

        # Create the Connections
        self.addConnection("negator", "DerivatorX", output_port_name='OUT1', input_port_name='IN1')
        self.addConnection("DerivatorV", "negator", output_port_name='OUT1', input_port_name='IN1')
        self.addConnection("DerivatorV", "V", output_port_name='OUT1')
        self.addConnection("constant0", "DerivatorX", output_port_name='OUT1', input_port_name='IC')
        self.addConnection("constant1", "DerivatorV", output_port_name='OUT1', input_port_name='IC')
        self.addConnection("DerivatorX", "DerivatorV", output_port_name='OUT1', input_port_name='IN1')
        self.addConnection("DerivatorX", "X", output_port_name='OUT1')
        self.addConnection("deltaT", "DerivatorX", output_port_name='OUT1', input_port_name='DT')
        self.addConnection("deltaT", "DerivatorV", output_port_name='OUT1', input_port_name='DT')


