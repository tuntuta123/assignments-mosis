import pandas as pd
import mtl

all_results = []

for i in range(1, 11):
    filename = f"simple_traffic_light_{i}.csv"
    # run from assignment-01/
    frame = pd.read_csv(f"data/ltl-simple-traffic-light/{filename}")

    trace = {
        "alternate" : list(zip(frame["step"], frame["alternate"].astype(bool))),
        "green" : list(zip(frame["step"], frame["green"].astype(bool))),
        "red" : list(zip(frame["step"], frame["red"].astype(bool))),
        "yellow" : list(zip(frame["step"], frame["yellow"].astype(bool))),
    }

    one_lamp = mtl.parse(
        "G[0,201] ("
        "((red & ~yellow) & ~green)"
        "| ((~red & yellow) & ~green)"
        "| ((~red & ~yellow) & green)"
        ")"
    )

    starts_red = mtl.parse(
        "G[0, 1] red"
    )

    always_red = mtl.parse(
        "G[0,201] red"
    )

    eventually_green = mtl.parse(
        "F[0,201] green"
    )

    red_stays_or_next_yellow = mtl.parse(
        "G[0,200] (red -> (X red | X yellow))"
    )

    no_red_to_green = mtl.parse(
        "G[0,200] (red -> ~X green)"
    )

    no_green_to_red = mtl.parse(
        "G[0,200] (green -> ~X red)"
    )

    yellow_opens_to_green = mtl.parse(
        "G[0,200] (((yellow & ~alternate) & ~X yellow) -> X green)"
    )

    yellow_returns_to_red = mtl.parse(
        "G[0,200] (((yellow & alternate) & ~X yellow) -> X red)"
    )

    yellow_after_red_may_wait = mtl.parse(
        "G[0, 200] ((red & X yellow) -> X (yellow W green))"
    )

    results = {
        "trace": filename,
        "one_lamp": one_lamp(trace, time=0, quantitative=False, dt=1),
        "starts_red": starts_red(trace, time=0, quantitative=False, dt=1),
        "always_red": always_red(trace, time=0, quantitative=False, dt=1),
        "eventually_green": eventually_green(trace, time=0, quantitative=False, dt=1),
        "red_stays_or_next_yellow": red_stays_or_next_yellow(trace, time=0, quantitative=False, dt=1),
        "no_red_to_green": no_red_to_green(trace, time=0, quantitative=False, dt=1),
        "no_green_to_red": no_green_to_red(trace, time=0, quantitative=False, dt=1),
        "yellow_opens_to_green": yellow_opens_to_green(trace, time=0, quantitative=False, dt=1),
        "yellow_returns_to_red": yellow_returns_to_red(trace, time=0, quantitative=False, dt=1),
        "yellow_after_red_may_wait": yellow_after_red_may_wait(trace, time=0, quantitative=False, dt=1)
    }

    all_results.append(results)

output = pd.DataFrame(all_results)

output = output.replace({True: "true", False: "false"})

output.to_csv(
    "results/simple_traffic_light_ltl.csv",
    index=False
)