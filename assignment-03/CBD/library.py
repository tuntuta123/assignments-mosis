"""
CBD Block library. 
"""

import math  # GenericBlock applies math.<block_operator> to its input

from .model import BaseBlock, CBD
from .fmi2 import FMU2CoSimulation
from pathlib import Path


__all__ = [
    "ConstantBlock",
    "AdderBlock",
    "NegatorBlock",
    "InverterBlock",
    "ProductBlock",
    "GenericBlock",
    "DelayBlock",
    "DeltaTBlock",
    "TimeBlock",
    "ScopeBlock",
    "IntegratorBlock",
    "DerivatorBlock",
]


class ConstantBlock(BaseBlock):
    """Always outputs ``value`` on ``OUT1``. Has no dependencies."""

    def __init__(self, block_name, value=0.0):
        BaseBlock.__init__(self, block_name, [], ["OUT1"])
        self._value = value

    def getValue(self):
        return self._value

    def setValue(self, value):
        self._value = value

    def compute(self, curIteration, time, delta_t):
        self.appendToSignal(self.getValue(), time=time)


class AdderBlock(BaseBlock):
    """Outputs the sum of inputs ``IN1`` .. ``INn`` on ``OUT1``."""

    def __init__(self, block_name, numberOfInputs=2):
        BaseBlock.__init__(self, block_name, ["IN%d" % (i + 1) for i in range(numberOfInputs)], ["OUT1"])
        self._numberOfInputs = numberOfInputs

    def getNumberOfInputs(self):
        return self._numberOfInputs

    def compute(self, curIteration, time, delta_t):
        total = 0.0
        for index in range(1, self._numberOfInputs + 1):
            total += self.getInputSignal(curIteration, "IN%d" % index).value
        self.appendToSignal(total, time=time)


class NegatorBlock(BaseBlock):
    """Outputs the negation of ``IN1``."""

    def __init__(self, block_name):
        BaseBlock.__init__(self, block_name, ["IN1"], ["OUT1"])

    def compute(self, curIteration, time, delta_t):
        self.appendToSignal(-self.getInputSignal(curIteration, "IN1").value, time=time)


class InverterBlock(BaseBlock):
    """Outputs ``1 / IN1``.
    Raises ``ZeroDivisionError`` when the absolute input is below ``tolerance``.
    """

    def __init__(self, block_name, tolerance=1e-30):
        BaseBlock.__init__(self, block_name, ["IN1"], ["OUT1"])
        self.tolerance = tolerance

    def compute(self, curIteration, time, delta_t):
        value = self.getInputSignal(curIteration, "IN1").value

        if abs(value) < self.tolerance:
            raise ZeroDivisionError("abs(input) < tolerance")

        self.appendToSignal(1 / value, time=time)
class ProductBlock(BaseBlock):
    """Outputs the product of inputs ``IN1`` .. ``INn``."""

    def __init__(self, block_name, numberOfInputs=2):
        BaseBlock.__init__(self, block_name, ["IN%d" % (i + 1) for i in range(numberOfInputs)], ["OUT1"])
        self._numberOfInputs = numberOfInputs

    def getNumberOfInputs(self):
        return self._numberOfInputs

    def compute(self, curIteration, time, delta_t):
        total = 1.0
        for index in range(1, self._numberOfInputs + 1):
                total *= self.getInputSignal(curIteration, "IN%d" % index).value
        self.appendToSignal(total, time=time)


class GenericBlock(BaseBlock):
    """Applies a one-argument function from the ``math`` module to ``IN1``.
    ``block_operator`` is the function name, for example ``"sin"`` or ``"cos"``.
    """

    def __init__(self, block_name, block_operator=None):
        BaseBlock.__init__(self, block_name, ["IN1"], ["OUT1"])
        self._block_operator = block_operator

    def getBlockOperator(self):
        return self._block_operator

    def compute(self, curIteration, time, delta_t):
        operation = getattr(math, self._block_operator)
        self.appendToSignal(operation(self.getInputSignal(curIteration, "IN1").value), time=time)


class DelayBlock(BaseBlock):
    """Outputs ``IC`` at iteration 0, and the previous ``IN1`` after that.
    The delay depends on the block behind ``IC`` at iteration 0 and on nothing
    afterwards. The value carried across the iteration comes from history, so
    a feedback wire through a delay is not an algebraic loop.
    """

    def __init__(self, block_name):
        BaseBlock.__init__(self, block_name, ["IN1", "IC"], ["OUT1"])

    def getDependencies(self, curIteration):
        if curIteration == 0:
            port = self.getInputPortByName("IC")
            source = port.getSourcePort()

            if source is not None:
                return [source.block]

        return []

    def compute(self, curIteration, time, delta_t):
        if curIteration == 0:
            value = self.getInputSignal(curIteration, "IC").value
        else:
            value = self.getInputSignal(curIteration - 1, "IN1").value

        self.appendToSignal(value, time=time)


class DeltaTBlock(BaseBlock):
    """Outputs the simulator step size. Has no inputs."""

    def __init__(self, block_name):
        BaseBlock.__init__(self, block_name, [], ["OUT1"])

    def compute(self, curIteration, time, delta_t):
        self.appendToSignal(delta_t, time=time)


class TimeBlock(BaseBlock):
    """Outputs the simulation time.
    ``OUT1`` and ``relative`` are both the time passed to ``compute``. The
    simulator starts at time 0, so the two outputs stay equal.
    """

    def __init__(self, block_name):
        BaseBlock.__init__(self, block_name, [], ["OUT1", "relative"])

    def compute(self, curIteration, time, delta_t):
        self.appendToSignal(time, name_output="OUT1", time=time)
        self.appendToSignal(time, name_output="relative", time=time)

# Part 2. Both blocks are hierarchical CBDs built from the blocks above.


class IntegratorBlock(CBD):
    """Forward-Euler integrator, built from library blocks.

    ``output[0] = IC``, and ``output[i] = output[i-1] + (delta_t * input[i-1])``.
    Inputs are ``IN1`` (the signal to integrate), ``IC``, and ``DT``. Output is ``OUT1``.
    """

    def __init__(self, block_name):
        CBD.__init__(self, block_name, input_ports=["IN1", "IC", "DT"], output_ports=["OUT1"])
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


class DerivatorBlock(CBD):
    """Discrete derivative, built from library blocks.

    ``output[0] = IC``, and ``output[i] = (input[i] - input[i-1]) / delta_t``.
    Inputs are ``IN1`` and ``IC``, and ``DT``. Output is ``OUT1``.
    """

    def __init__(self, block_name):
        CBD.__init__(self, block_name, input_ports=["IN1", "IC", "DT"], output_ports=["OUT1"])
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
        


# Part 4: Task 3

class ScopeBlock(BaseBlock):
    """Marks ``IN1`` for tracing. There is no output.

    ``k`` is how many integration steps pass between traces. The simulator
    reads :meth:`getK` and calls :meth:`compute` on those steps. Each call
    appends the current input to the trace.
    """

    def __init__(self, block_name, k=1):
        BaseBlock.__init__(self, block_name, ["IN1"], [])
        self._k = k
        self._trace = []

    def getK(self):
        return self._k

    def getTrace(self):
        return list(self._trace)

    def compute(self, curIteration, time, delta_t):
        self._trace.append(self.getInputSignal(curIteration, "IN1"))


# Part 4: Task 4

class FMUBlock(BaseBlock):
    """One co-simulation FMU with a scalar input and a scalar output.

    ``getDependencies`` is empty at every iteration, the same way a delay
    depends on nothing after iteration 0. The block therefore reads the
    input that was computed on the previous iteration. A plant with direct
    feedthrough would list its input block here and the feedback would be
    an algebraic loop.
    """

    def __init__(self, block_name, fmu_path=None, input_name="u", output_name="y"):
        BaseBlock.__init__(self, block_name, ["IN1"], ["OUT1"])
        if fmu_path is None:
            raise ValueError("FMU path is required")
        self._fmu_path = Path(fmu_path)
        self._input_name = input_name
        self._output_name = output_name
        self._fmu = None
        self._input_reference = None
        self._output_reference = None

    def getDependencies(self, curIteration):
        return []

    def compute(self, curIteration, time, delta_t):
        #TODO: Part 4, Task 4
        raise NotImplementedError("FMUBlock.compute")

    def _open(self):
        if self._fmu is not None:
            return
        self._fmu = FMU2CoSimulation(self._fmu_path)
        self._input_reference = self._fmu.value_references[self._input_name]
        self._output_reference = self._fmu.value_references[self._output_name]
        self._fmu.instantiate()
        self._fmu.setup()

    def close(self):
        if self._fmu is None:
            return
        try:
            self._fmu.terminate()
        finally:
            self._fmu.free()
            self._fmu = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
