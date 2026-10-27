#!/usr/bin/python3
# This file was automatically generated from drawio2cbd with the command:
#   __main__.py ../diagrams/Derivator.drawio -F CBD -e Derivator -d ../generated

from CBD.model import *
from CBD.library import *


class Derivator(CBD):
    def __init__(self, block_name):
        super().__init__(block_name, input_ports=['IN1', 'DT', 'IC'], output_ports=['OUT1'])

        # Create the Blocks
        self.addBlock(AdderBlock("adder1", numberOfInputs=(2)))
        self.addBlock(DelayBlock("delay1"))
        self.addBlock(NegatorBlock("negator1"))
        self.addBlock(ProductBlock("product1", numberOfInputs=(2)))
        self.addBlock(InverterBlock("inverter1"))
        self.addBlock(ProductBlock("product2", numberOfInputs=(2)))
        self.addBlock(NegatorBlock("negator2"))
        self.addBlock(AdderBlock("adder2", numberOfInputs=(2)))

        # Create the Connections
        self.addConnection("IN1", "delay1", input_port_name='IN1')
        self.addConnection("IN1", "adder1", input_port_name='IN1')
        self.addConnection("IN1", "adder2", input_port_name='IN1')
        self.addConnection("DT", "inverter1", input_port_name='IN1')
        self.addConnection("DT", "product2", input_port_name='IN1')
        self.addConnection("IC", "product2", input_port_name='IN2')
        self.addConnection("delay1", "negator1", output_port_name='OUT1', input_port_name='IN1')
        self.addConnection("negator1", "adder1", output_port_name='OUT1', input_port_name='IN2')
        self.addConnection("inverter1", "product1", output_port_name='OUT1', input_port_name='IN1')
        self.addConnection("adder1", "product1", output_port_name='OUT1', input_port_name='IN2')
        self.addConnection("product1", "OUT1", output_port_name='OUT1')
        self.addConnection("product2", "negator2", output_port_name='OUT1', input_port_name='IN1')
        self.addConnection("negator2", "adder2", output_port_name='OUT1', input_port_name='IN2')
        self.addConnection("adder2", "delay1", output_port_name='OUT1', input_port_name='IC')


