"""
Linear algebraic loop solver. 

"""

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
    # TODO: Part 1, Task 3
    raise NotImplementedError("is_linear")


def build_system(component, curIteration):
    """Return ``(A, b)`` for ``A x = b``.

    Row ``i`` is the equation of ``component[i]``, 
    and ``x[i]`` is that block's output. 
    """
    # TODO: Part 1, Task 3
    raise NotImplementedError("build_system")

def solve_linear_loop(component, curIteration, time, matrix=None):
    """Solve the loop and append one output per block.

    Without ``matrix``, build the whole system. With ``matrix``, reuse that
    ``A`` and rebuild ``b``. Raise ``ValueError`` when the system is singular.
    """
    # TODO: Part 1, Task 3
    raise NotImplementedError("solve_linear_loop")


if __name__ == "__main__":
    print("Implement is_linear, build_system, rebuild_rhs and solve_linear_loop.")
