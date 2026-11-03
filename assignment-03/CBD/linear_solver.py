"""
Linear algebraic loop solver. 

"""
from .library import (
    AdderBlock,
    DelayBlock,
    GenericBlock,
    InverterBlock,
    NegatorBlock,
    ProductBlock,
)
import numpy as np

__all__ = [
    "is_linear",
    "build_system",
    "rebuild_rhs",
    "solve_linear_loop",
]


def is_linear(component):
    """Return True when every block in the loop has a linear equation.

    An adder, a negator and a delay are linear. A product is linear only when
    fewer than two of its inputs are unknowns of this same loop. An inverter,
    a generic block, or a product of two unknowns is not linear.
    """

    component_blocks = set(component)

    for block in component:
        if isinstance(block, (AdderBlock, NegatorBlock, DelayBlock)):
            continue

        if isinstance(block, ProductBlock):
            unknown_inputs = sum(
                1
                for port in block.getInputPorts()
                if (source := port.getSourcePort()) is not None
                and source.block in component_blocks
            )
            if unknown_inputs < 2:
                continue

        # raise ValueError(f"Unsupported or nonlinear block type: {block.getBlockType()}")
        return False

    return True


def build_system(component, curIteration):
    """Return ``(A, b)`` for ``A x = b``.

    Row ``i`` is the equation of ``component[i]``, 
    and ``x[i]`` is that block's output. 
    """

    size = len(component)
    column = {block: i for i, block in enumerate(component)}
    A = np.zeros((size, size))
    b = np.zeros(size)

    for i, block in enumerate(component):
        A[i, i] = -1.0

        if isinstance(block, DelayBlock):
            input_name = "IC" if curIteration == 0 else "IN1"
            input_iteration = 0 if curIteration == 0 else curIteration - 1
            source = block.getInputPortByName(input_name).getSourcePort()

            if curIteration == 0 and source is not None and source.block in column:
                A[i, column[source.block]] += 1.0
            else:
                b[i] = -block.getInputSignal(input_iteration, input_name).value

            continue

        unknown = []
        known = []

        for port in block.getInputPorts():
            source = port.getSourcePort()
            if source is not None and source.block in column:
                unknown.append(column[source.block])
            else:
                known.append(block.getInputSignal(curIteration, port.name).value)

        if isinstance(block, AdderBlock):
            for j in unknown:
                A[i, j] += 1.0
            b[i] = -sum(known)

        elif isinstance(block, NegatorBlock):
            for j in unknown:
                A[i, j] -= 1.0
            b[i] = sum(known)

        elif isinstance(block, ProductBlock):
            if unknown:
                A[i, unknown[0]] += np.prod(known)
            else:
                b[i] = -np.prod(known)

        else:
            raise ValueError(f"Unsupported block type: {block.getBlockType()}")

    return A, b


def rebuild_rhs(component, curIteration):
    """Rebuilding the right hand side (Rhs)
        A remains unchanged, so it can be cached. However RHS needs to be rebuilt every step
    """
    size = len(component)
    component_blocks = set(component)
    b = np.zeros(size)

    for i, block in enumerate(component):

        if isinstance(block, DelayBlock):
            input_name = "IC" if curIteration == 0 else "IN1"
            input_iteration = 0 if curIteration == 0 else curIteration - 1
            source = block.getInputPortByName(input_name).getSourcePort()

            if not (curIteration == 0 and source is not None and source.block in component_blocks):
                b[i] = -block.getInputSignal(input_iteration, input_name).value

            continue

        known = []
        unknown_count = 0

        for port in block.getInputPorts():
            source = port.getSourcePort()

            if source is not None and source.block in component_blocks:
                unknown_count += 1
            else:
                known.append(block.getInputSignal(curIteration, port.name).value)

        if isinstance(block, AdderBlock):
            b[i] = -sum(known)

        elif isinstance(block, NegatorBlock):
            b[i] = sum(known)

        elif isinstance(block, ProductBlock):
            if unknown_count == 0:
                b[i] = -np.prod(known)

        else:
            raise ValueError(
                f"Unsupported block type: {block.getBlockType()}"
            )

    return b



def solve_linear_loop(component, curIteration, time, matrix=None):
    """Solve the loop and append one output per block.

    Without ``matrix``, build the whole system. With ``matrix``, reuse that
    ``A`` and rebuild ``b``. Raise ``ValueError`` when the system is singular.
    """
    #check cache
    if matrix is None:
        A, b = build_system(component, curIteration)
    else:
        A = matrix
        b = rebuild_rhs(component, curIteration)
    try:
        x = np.linalg.solve(A, b)
    except np.linalg.LinAlgError as err:
        raise ValueError("Algebraic loop has no unique solution") from err

    for block, value in zip(component, x):
        block.appendToSignal(float(value), time=time)

    return A
# if __name__ == "__main__":
#     print("Implement is_linear, build_system, rebuild_rhs and solve_linear_loop.")
