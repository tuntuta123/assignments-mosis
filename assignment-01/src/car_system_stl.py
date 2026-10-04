import mtl
import pandas as pd

all_results = []

filenames = [
    "car_system_kp100_ki1_kd100.csv",
    "car_system_kp210_ki1_kd1.csv",
    "car_system_kp250_ki5_kd5.csv",
    "car_system_kp280_ki10_kd10.csv",
    "car_system_kp300_ki1_kd20.csv",
    "car_system_kp300_ki20_kd1.csv",
    "car_system_kp320_ki15_kd5.csv",
    "car_system_kp350_ki20_kd10.csv",
    "car_system_kp370_ki10_kd15.csv",
    "car_system_kp390_ki5_kd20.csv",
]

for filename in filenames:
    frame = pd.read_csv(f"data/stl-car-system/{filename}")

    print(filename)

    trace = {
        "safe_space" : list(zip(frame["time"], frame["intervehicular_distance.y"] >= 9)),
        "safe_accel" : list(zip(frame["time"], frame["ego_car.accSensor.a"].abs() <= 10)),
        "necessary_gap" : list(zip(frame["time"], (10 - frame["intervehicular_distance.y"]).abs() <= 0.5)),
        "settled_loose" : list(zip(frame["time"], (10 - frame["intervehicular_distance.y"]).abs() <= 1)),
    }

    reaches_soon = mtl.parse("F[0,20.1] necessary_gap")

    settled_tight = mtl.parse("G[30,60.1] necessary_gap")

    settled_loose = mtl.parse("G[20,60.1] settled_loose")

    keeps_distance = mtl.parse("G[0,60.1] safe_space")

    accel_bounded = mtl.parse("G[0,60.1] safe_accel")

    results = {
        "trace": filename,
        "reaches_soon": reaches_soon(trace, time=0, quantitative=False),
        "settled_tight": settled_tight(trace, time=0, quantitative=False),
        "settled_loose": settled_loose(trace, time=0, quantitative=False),
        "keeps_distance": keeps_distance(trace, time=0, quantitative=False),
        "accel_bounded": accel_bounded(trace, time=0, quantitative=False),
    }

    all_results.append(results)

output = pd.DataFrame(all_results)
#print(output)

output = output.replace({True: "true", False: "false"})


output.to_csv("results/car_system_stl.csv", index=False)