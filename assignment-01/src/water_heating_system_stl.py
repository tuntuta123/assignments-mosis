import mtl
import pandas as pd

all_results = []

filenames = [
    "water_heating_system_kp50_ki50_kd10.csv",
    "water_heating_system_kp100_ki0_kd10.csv",
    "water_heating_system_kp100_ki1_kd40.csv",
    "water_heating_system_kp100_ki5_kd10.csv",
    "water_heating_system_kp100_ki20_kd10.csv",
    "water_heating_system_kp200_ki2_kd40.csv",
    "water_heating_system_kp300_ki0_kd45.csv",
    "water_heating_system_kp300_ki10_kd20.csv",
    "water_heating_system_kp500_ki0_kd50.csv",
    "water_heating_system_kp500_ki5_kd0.csv",
]

for filename in filenames:
    frame = pd.read_csv(f"data/stl-water-system/{filename}")

    print(filename)

    trace = {
            "reaches_setpoint": list(zip(frame["time"], frame["plant_block1.T_out"] >= 321.15)),
            "safe_temp" : list(zip(frame["time"], frame["plant_block1.T_out"] <= 330)),
            "settled" : list(zip(frame["time"], (323.15 - frame["plant_block1.T_out"]).abs() <= 3)), ##abs(323-t) <= 3 
            "level_low" : list(zip(frame["time"], frame["plant_block1.level_out"] >= 1.4)),
            "level_high" : list(zip(frame["time"], frame["plant_block1.level_out"] <= 2.9)),
            "heater_on" : list(zip(frame["time"], frame["pid_controller1.limiter.y"] >= 150)),
        }

    reaches_setpoint = mtl.parse("F[0,86400.1] reaches_setpoint")
    no_temperature_overshoot = mtl.parse("G[0, 86400.1] safe_temp")
    settled_after_half_day = mtl.parse("G[43200, 86400.1] settled")
    level_in_band = mtl.parse("G[0, 86400.1] (level_low & level_high)")
    heater_stays_on = mtl.parse("G[0, 86400.1] heater_on")

results = {

        #todo
        
    }

output = pd.DataFrame(all_results)
#print(output)

output = output.replace({True: "true", False: "false"})

output.to_csv("results/water_heating_system_stl.csv", index=False)