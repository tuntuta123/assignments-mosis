"""
The CBD model: signals, ports, wires, blocks and nested CBDs.
"""

from collections import namedtuple


Signal = namedtuple("Signal", ["time", "value"])

__all__ = [
    "Signal",
    "Port",
    "Connection",
    "BaseBlock",
    "CBD",
]


class Port:
    """One input or output of a block.

    ``set`` records a signal on this port only. It does not walk the
    connections. 
    
    Inputs are read by resolving ``getSourcePort`` back to the
    atomic block that produced the value.

    CBD output ports are filled afterwards by the simulator.
    """

    IN = "IN"
    OUT = "OUT"

    def __init__(self, name, direction, block):
        self.name = name
        self.direction = direction
        self.block = block
        self._incoming = None
        self._outgoing = []
        self._history = []

    def __repr__(self):
        return "Port(%s)" % self.getPath()

    def getPath(self, sep="."):
        return self.block.getPath(sep) + sep + self.name

    def set(self, value):
        """Append ``value`` (a :class:`Signal`) to this port's history."""
        self._history.append(value)

    def get(self):
        """Return the most recent signal."""
        return self._history[-1]

    def getHistory(self):
        return self._history

    def getIncoming(self):
        """The :class:`Connection` that feeds this port, or ``None``."""
        return self._incoming

    def getOutgoing(self):
        return list(self._outgoing)

    def getSourcePort(self):
        """
        Walk incoming connections to the port that produces the value for this port.
        """
        incoming = self.getIncoming()

        if incoming is None: #no incoming connection
            return None  

        source = incoming.source

        if isinstance(source.block, CBD): #cbd check
            return source.getSourcePort()

        return source

    @staticmethod
    def connect(source, target):
        """Connect ``source`` to ``target``. An input accepts one connection."""
        if target._incoming is not None:
            raise ValueError("Port '%s' is already connected." % target.getPath())
        connection = Connection(source, target)
        source._outgoing.append(connection)
        target._incoming = connection


class Connection:
    """A directed wire from an output (or a parent input) to a target port."""

    def __init__(self, source, target):
        self.source = source
        self.target = target

    def __repr__(self):
        return "Connection(%s -> %s)" % (self.source, self.target)


class BaseBlock:
    """A named block with input and output ports.

    ``compute`` receives the iteration, the absolute simulation time and the
    step size, and appends one signal per output. 
    
    ``getDependencies`` returns the atomic blocks that must be computed before 
    this one at the given iteration.
    """

    def __init__(self, name, input_ports, output_ports):
        self._name = name
        self._parent = None
        self._inputs = {}
        self._outputs = {}
        for port_name in input_ports:
            self._inputs[port_name] = Port(port_name, Port.IN, self)
        for port_name in output_ports:
            self._outputs[port_name] = Port(port_name, Port.OUT, self)

    def __repr__(self):
        return "%s:%s" % (self.getPath(), self.getBlockType())

    def getBlockName(self):
        return self._name

    def getBlockType(self):
        return self.__class__.__name__

    def setParent(self, parent):
        self._parent = parent

    def getPath(self, sep="."):
        if self._parent is None:
            return self.getBlockName()
        return self._parent.getPath(sep) + sep + self.getBlockName()

    def getInputPorts(self):
        return list(self._inputs.values())

    def getOutputPorts(self):
        return list(self._outputs.values())

    def getInputPortNames(self):
        return list(self._inputs.keys())

    def getOutputPortNames(self):
        return list(self._outputs.keys())

    def hasInputPortWithName(self, name):
        return name in self._inputs

    def hasOutputPortWithName(self, name):
        return name in self._outputs

    def getInputPortByName(self, name):
        if name not in self._inputs:
            raise ValueError("No input '%s' on '%s'." % (name, self.getPath()))
        return self._inputs[name]

    def getOutputPortByName(self, name):
        if name not in self._outputs:
            raise ValueError("No output '%s' on '%s'." % (name, self.getPath()))
        return self._outputs[name]

    def appendToSignal(self, value, name_output=None, time=0.0):
        """Record ``value`` on an output. Defaults to ``OUT1``."""
        if name_output is None:
            name_output = "OUT1"
        self.getOutputPortByName(name_output).set(Signal(time, value))

    def getSignalHistory(self, name_output=None):
        """Return the list of :class:`Signal` sent on an output."""
        if name_output is None:
            name_output = "OUT1"
        return self.getOutputPortByName(name_output).getHistory()

    def getInputSignal(self, curIteration=-1, input_port="IN1"):
        """Return the signal currently available on an input.

        The input is followed through CBD ports (using the ``getSourcePort`` method) 
        until the output port of an atomic block that produces the input signal. 
        
        ``curIteration`` selects that output's history index. 
        ``-1`` selects the latest sample.
        """
        # TODO: Part 1, Task 2
        raise NotImplementedError("BaseBlock.getInputSignal")

    def getDependencies(self, curIteration):
        """Atomic blocks that feed this block at ``curIteration``.
 
        Follow each connected input with ``getSourcePort`` and return the
         atomic block that owns that output. Do not return a CBD!. 
        
        Note that``DelayBlock`` overrides this method, because a delay does not 
        read every input at every iteration.
        """
        dependencies = []

        for port in self.getInputPorts():
            source = port.getSourcePort()

        if source is not None:
            dependencies.append(source.block)

        return dependencies

    def defaultInputPortNameIdentifier(self):
        """Name of the first input ``INx`` that is still unconnected."""
        index = 1
        while True:
            port_name = "IN%d" % index
            if not self.hasInputPortWithName(port_name):
                raise ValueError("No free input left on '%s'." % self.getPath())
            if self.getInputPortByName(port_name).getIncoming() is None:
                return port_name
            index += 1

    def linkToInput(self, in_block, name_input=None, name_output="OUT1"):
        """Connect ``name_output`` of ``in_block`` to ``name_input`` of this block.

        A parent input may be used as a source, and a parent output may be
        used as a target. Those two cases are how hierarchy crosses a CBD
        boundary.
        """
        if name_input is None:
            name_input = self.defaultInputPortNameIdentifier()
        if in_block.hasOutputPortWithName(name_output):
            source = in_block.getOutputPortByName(name_output)
        elif (self._parent is in_block or in_block is self) and in_block.hasInputPortWithName(name_output):
            source = in_block.getInputPortByName(name_output)
        else:
            raise ValueError(
                "Cannot take output '%s' from '%s'." % (name_output, in_block.getPath())
            )
        if self.hasInputPortWithName(name_input):
            target = self.getInputPortByName(name_input)
        elif (self is in_block._parent or self is in_block) and self.hasOutputPortWithName(name_input):
            target = self.getOutputPortByName(name_input)
        else:
            raise ValueError("Cannot connect to '%s' on '%s'." % (name_input, self.getPath()))
        Port.connect(source, target)

    def compute(self, curIteration, time, delta_t):
        raise NotImplementedError("BaseBlock has nothing to compute")


class CBD(BaseBlock):
    """A block that contains other blocks.

    ``input_ports`` and ``output_ports`` are the boundary of this level.
    Connecting a child to one of those names wires the hierarchy.
    """

    def __init__(self, block_name, input_ports=None, output_ports=None):
        if input_ports is None:
            input_ports = []
        if output_ports is None:
            output_ports = []
        BaseBlock.__init__(self, block_name, input_ports, output_ports)
        self._order = []
        self._blocks = {}

    def addBlock(self, block):
        if not isinstance(block, BaseBlock):
            raise TypeError("Can only add blocks, not %s." % type(block).__name__)
        name = block.getBlockName()
        if name in self._blocks or self.hasInputPortWithName(name) or self.hasOutputPortWithName(name):
            raise ValueError("Name '%s' is already used in '%s'." % (name, self.getPath()))
        block.setParent(self)
        self._order.append(block)
        self._blocks[name] = block
        return block

    def getBlocks(self):
        return list(self._order)

    def getBlockByName(self, name):
        if name not in self._blocks:
            raise ValueError("No block named '%s' in '%s'." % (name, self.getPath()))
        return self._blocks[name]

    def addConnection(self, from_block, to_block, input_port_name=None, output_port_name="OUT1"):
        """Connect an output of ``from_block`` to an input of ``to_block``.

        Both arguments are block names, or the name of a port of this CBD.
        An input-port name used as ``from_block`` connects that parent input.
        An output-port name used as ``to_block`` connects that parent output.
        ``output_port_name`` defaults to ``OUT1``. ``input_port_name``
        defaults to the first free ``INx`` input.
        """
        if isinstance(from_block, str):
            if self.hasInputPortWithName(from_block):
                output_port_name = from_block
                from_block = self
            else:
                from_block = self.getBlockByName(from_block)
        if isinstance(to_block, str):
            if self.hasOutputPortWithName(to_block):
                input_port_name = to_block
                to_block = self
            else:
                to_block = self.getBlockByName(to_block)
        to_block.linkToInput(from_block, name_input=input_port_name, name_output=output_port_name)

    def compute(self, curIteration, time, delta_t):
        raise NotImplementedError(
            "CBD '%s' is not computed directly. Compute the atomic blocks it contains."
            % self.getPath()
        )
