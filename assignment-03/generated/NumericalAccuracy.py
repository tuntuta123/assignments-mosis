import numpy as np
import pandas as pd

from OscillatorIntegral import OscillatorIntegral
from OscillatorDerivative import OscillatorDerivative
from CBD.simulator import Simulator

STEP_SIZES = [0.1, 0.01, 0.001]
T_END = 20.0
OUTPUT_FILE = "NumericalAccuracy_table.csv"

MODELS = [
    ("Integral", OscillatorIntegral, "X", "V", -1.0),
    ("Derivative", OscillatorDerivative, "X", "V", 1.0),
]


def run(cls, x_port, v_port, delta_t):
    cbd = cls(cls.__name__)
    sim = Simulator(cbd)
    sim.setDeltaT(delta_t)
    sim.run(T_END)
    x = np.array([s.value for s in cbd.getSignalHistory(x_port)])
    v = np.array([s.value for s in cbd.getSignalHistory(v_port)])
    t = np.arange(len(x)) * delta_t
    return t, x, v


rows = []
for name, cls, x_port, v_port, sign in MODELS:
    for dt in STEP_SIZES:
        t, x, v = run(cls, x_port, v_port, dt)
        rows.append(
            {
                "Model": name,
                "dt": dt,
                "MSE x": np.mean((x - sign * np.sin(t)) ** 2),
                "MSE v": np.mean((v - np.cos(t)) ** 2),
            }
        )

df = pd.DataFrame(rows)
df.to_csv(OUTPUT_FILE, index=False)
# print(df.to_string(index=False, float_format=lambda value: f"{value:.3e}"))