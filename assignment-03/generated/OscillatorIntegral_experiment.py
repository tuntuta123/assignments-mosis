from matplotlib import pyplot as plt

from OscillatorIntegral import *
from CBD.simulator import Simulator

MODEL = OscillatorIntegral
MODEL_NAME = "OscillatorIntegral"
STEP_SIZES = [0.1, 0.01, 0.001]
T_END = 20.0


def simulate(delta_t):
    cbd = MODEL(MODEL_NAME)
    sim = Simulator(cbd)
    sim.setDeltaT(delta_t)
    sim.run(T_END)

    x = [s.value for s in cbd.getSignalHistory("X")]
    v = [s.value for s in cbd.getSignalHistory("V")]
    t = [i * delta_t for i in range(len(x))]
    return t, x, v


results = {}
for dt in STEP_SIZES:
    try:
        results[dt] = simulate(dt)
    except ValueError as e:
        print(f"dt={dt}: {e}")
        raise SystemExit(1)

fig, axes = plt.subplots(2, 3, figsize=(15, 8))
for col, dt in enumerate(STEP_SIZES):
    t, x, v = results[dt]

    axes[0][col].plot(t, x)
    axes[0][col].set_title(f"x(t), dt = {dt}")
    axes[0][col].set_xlabel("t")
    axes[0][col].set_ylabel("x")
    axes[0][col].grid(True)

    axes[1][col].plot(x, v)
    axes[1][col].set_title(f"Phase plot, dt = {dt}")
    axes[1][col].set_xlabel("x")
    axes[1][col].set_ylabel("v")
    axes[1][col].set_aspect("equal", adjustable="datalim")
    axes[1][col].grid(True)

fig.suptitle(f"{MODEL_NAME}: oscillator")
fig.tight_layout()
fig.savefig(f"{MODEL_NAME}_plots.png", dpi=150)
plt.show()