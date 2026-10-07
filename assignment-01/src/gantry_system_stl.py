import pandas as pd
import mtl
import os

all_results = []

data_dir = "data/stl-gantry-crane-system"
filenames = sorted(os.listdir(data_dir))

for filename in filenames:
    # run from assignment-01/
    frame = pd.read_csv(f"{data_dir}/{filename}")
    # print(filename)

    trace = {
        "angle_half": list(zip(frame["time"], frame["gantry.theta"].abs() <= 0.5)),
        "angle_limit": list(zip(frame["time"], frame["gantry.theta"].abs() <= 1.5)),
        "reached_target": list(zip(frame["time"], frame["gantry.x"] >= 9.5)),
        "is_settled": list(zip(frame["time"], (frame["gantry.x"] >= 9.5) & (frame["gantry.x"] <= 10.5))),
        "under_overshoot": list(zip(frame["time"], frame["gantry.x"] <= 10.5)),
    }

    angle_within_half = mtl.parse(
        "G[0, 20.1] angle_half"
    )

    angle_within_limit = mtl.parse(
        "G[0, 20.1] angle_limit"
    )

    reaches_by_8s = mtl.parse(
        "F[0, 8.01] reached_target"
    )

    settled = mtl.parse(
        "G[10, 20.1] is_settled"
    )

    no_overshoot = mtl.parse(
        "G[0, 20.1] under_overshoot"
    )

    results = {
        "trace": filename,
        "angle_within_half": angle_within_half(trace, time=0, quantitative=False),
        "angle_within_limit": angle_within_limit(trace, time=0, quantitative=False),
        "reaches_by_8s": reaches_by_8s(trace, time=0, quantitative=False),
        "settled": settled(trace, time=0, quantitative=False),
        "no_overshoot": no_overshoot(trace, time=0, quantitative=False)
    }
    # print(filename)
    all_results.append(results)

output = pd.DataFrame(all_results)

output = output.replace({True: "true", False: "false"})

output.to_csv(
    "results/gantry_system_stl.csv",
    index=False
)