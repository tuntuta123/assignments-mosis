from CBD.simulator import *
from generated.OscillatorIntegral import *
from generated.OscillatorDerivative import *


def check_loops(model):
    simulator = Simulator(model)

    for iteration in [0, 1]:
        graph = simulator._build_dependency_graph(iteration)
        components = strongly_connected_components(graph)

        loops = []

        for component in components:
            if is_algebraic_loop(component, graph):
                loops.append(component)

        print(f"\nmodel: {model.getBlockName()}")
        print(f"iteration: {iteration}")
        print(f"algebraic loops found: {len(loops)}")

        for loop in loops:
            print("algebraic loop:")
            for block in loop:
                print(" -", block.getPath())


integral = OscillatorIntegral("Integral")
derivative = OscillatorDerivative("Derivative")

check_loops(integral)
check_loops(derivative)
