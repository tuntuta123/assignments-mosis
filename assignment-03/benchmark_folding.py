
import time
import numpy as np

from CBD.model import *
from CBD.library import *
from CBD.simulator import Simulator as NormalSimulator
from CBD.optimized_simulator import Simulator as OptimizedSimulator


def make_model():
    model = CBD("Benchmark")

    model.addBlock(ConstantBlock("c", 2))
    model.addBlock(TimeBlock("time"))

    # chain of 10 adders using only constant inputs
    # every block in this chain can be folded

    previous = "c"
    for i in range(10):
        name = f"add{i}"
        model.addBlock(AdderBlock(name, 2))
        model.addConnection(previous, name, input_port_name="IN1")
        model.addConnection("c", name, input_port_name="IN2")
        previous = name

    # algebraic loop

    model.addBlock(AdderBlock("sum", 2))
    model.addBlock(ProductBlock("product", 2))

    model.addConnection("time", "sum", input_port_name="IN1")
    model.addConnection("product", "sum", input_port_name="IN2")
    model.addConnection("sum", "product", input_port_name="IN1")
    model.addConnection(previous, "product", input_port_name="IN2")

    return model


def measure(simulator_class):
    model = make_model()
    simulator = simulator_class(model)

    start = time.perf_counter()
    simulator.run(300)
    elapsed = time.perf_counter() - start

    values = [s.value for s in model.getBlockByName("sum").getSignalHistory()]
    return elapsed, values


normal_times = []
optimized_times = []

for _ in range(100):
    normal_time, normal_values = measure(NormalSimulator)
    optimized_time, optimized_values = measure(OptimizedSimulator)

    assert np.allclose(normal_values, optimized_values)

    normal_times.append(normal_time)
    optimized_times.append(optimized_time)

normal_avg = np.mean(normal_times)
optimized_avg = np.mean(optimized_times)

print(f"normal: {normal_avg:.6f} s")
print(f"optimized: {optimized_avg:.6f} s")
print(f"speedup: {normal_avg / optimized_avg:.2f}x")
