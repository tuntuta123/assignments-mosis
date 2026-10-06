import pandas as pd
import mtl

all_results = []

for i in range(1, 11):
    filename = f"production_system_pipelined_{i}.csv"
    # run from assignment-01/
    frame = pd.read_csv(f"data/ltl-production-system-pipelined/{filename}")

    trace = {
        "m1_busy": list(zip(frame["step"], frame["m1_busy"].astype(bool))),
        "m1_down": list(zip(frame["step"], frame["m1_down"].astype(bool))),
        "m1_idle": list(zip(frame["step"], frame["m1_idle"].astype(bool))),
        "m1_repair": list(zip(frame["step"], frame["m1_repair"].astype(bool))),

        "m2_busy": list(zip(frame["step"], frame["m2_busy"].astype(bool))),
        "m2_down": list(zip(frame["step"], frame["m2_down"].astype(bool))),
        "m2_idle": list(zip(frame["step"], frame["m2_idle"].astype(bool))),
        "m2_repair": list(zip(frame["step"], frame["m2_repair"].astype(bool))),

        "p_buffer": list(zip(frame["step"], frame["p_buffer"].astype(bool))),
        "p_in": list(zip(frame["step"], frame["p_in"].astype(bool))),
        "p_m1": list(zip(frame["step"], frame["p_m1"].astype(bool))),
        "p_m2": list(zip(frame["step"], frame["p_m2"].astype(bool))),
        "p_out": list(zip(frame["step"], frame["p_out"].astype(bool))),

        "tech_busy": list(zip(frame["step"], frame["tech_busy"].astype(bool))),
        "tech_free": list(zip(frame["step"], frame["tech_free"].astype(bool))),
    }

    m1_one_mode = mtl.parse(
        "G[0,201] ("
        "(m1_busy & ~m1_down & ~m1_idle & ~m1_repair) "
        "| (~m1_busy & m1_down & ~m1_idle & ~m1_repair)"
        "| (~m1_busy & ~m1_down & m1_idle & ~m1_repair) "
        "| (~m1_busy & ~m1_down & ~m1_idle & m1_repair)"
        ")"
    )

    not_both_in_repair = mtl.parse(
        "G[0,201] (~(m1_repair & m2_repair))"
    )

    both_machines_holding = mtl.parse(
        "F[0,201] (p_m1 & p_m2)"
    )

    m1_while_buffer_full = mtl.parse(
        "F[0,201] (p_m1 & p_buffer)"
    )

    # assuming a part leaving ALWAYS leaves the stage empty for at least one step
    m1_to_buffer = mtl.parse(
        "G[0,200] ((p_m1 & ~X p_m1) -> ((m1_busy & ~p_buffer) & X p_buffer))"
    )

    ship_removes_only_out = mtl.parse(
        "G[0,200] ("
        "(p_out & ~X p_out) -> ("
        "(p_in <-> X p_in) & (p_m1 <-> X p_m1) & (p_buffer <-> X p_buffer) & (p_m2 <-> X p_m2)"
        ")"
        ")"
    )

    arrival_only_fills_in = mtl.parse(
        "G[0,200] ("
        "(~p_in & X p_in) -> ("
        "(p_m1 <-> X p_m1) & (p_buffer <-> X p_buffer) & (p_m2 <-> X p_m2) & (p_out <-> X p_out)"
        ")"
        ")"
    )

    results = {
        "trace": filename,
        "m1_one_mode": m1_one_mode(trace, time=0, quantitative=False, dt=1),
        "not_both_in_repair": not_both_in_repair(trace, time=0, quantitative=False, dt=1),
        "both_machines_holding": both_machines_holding(trace, time=0, quantitative=False, dt=1),
        "m1_while_buffer_full": m1_while_buffer_full(trace, time=0, quantitative=False, dt=1),
        "m1_to_buffer": m1_to_buffer(trace, time=0, quantitative=False, dt=1),
        "ship_removes_only_out": ship_removes_only_out(trace, time=0, quantitative=False, dt=1),
        "arrival_only_fills_in": arrival_only_fills_in(trace, time=0, quantitative=False, dt=1)
    }

    all_results.append(results)

output = pd.DataFrame(all_results)

output = output.replace({True: "true", False: "false"})

output.to_csv(
    "results/production_system_pipelined_ltl.csv",
    index=False
)