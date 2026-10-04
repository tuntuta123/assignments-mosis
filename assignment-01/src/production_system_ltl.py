import pandas as pd
import mtl

all_results = []

for i in range(1, 11):
    filename = f"production_system_{i}.csv"

    frame = pd.read_csv(f"data/ltl-simple-prod/{filename}")
    #run from assignment-01/

    trace = {
        "m1_busy" : list(zip(frame["step"], frame["m1_busy"].astype(bool))),
        "m1_down" : list(zip(frame["step"], frame["m1_down"].astype(bool))),
        "m1_idle" : list(zip(frame["step"], frame["m1_idle"].astype(bool))),
        "m1_repair" : list(zip(frame["step"], frame["m1_repair"].astype(bool))),

        "m2_busy" : list(zip(frame["step"], frame["m2_busy"].astype(bool))),
        "m2_down" : list(zip(frame["step"], frame["m2_down"].astype(bool))),
        "m2_idle" : list(zip(frame["step"], frame["m2_idle"].astype(bool))),
        "m2_repair" : list(zip(frame["step"], frame["m2_repair"].astype(bool))),

        "p_in" : list(zip(frame["step"], frame["p_in"].astype(bool))),
        "p_m1" : list(zip(frame["step"], frame["p_m1"].astype(bool))),
        "p_m2" : list(zip(frame["step"], frame["p_m2"].astype(bool))),
        "p_out" : list(zip(frame["step"], frame["p_out"].astype(bool))),

        "idle" : list(zip(frame["step"], frame["idle"].astype(bool))),
        "tech_busy" : list(zip(frame["step"], frame["tech_busy"].astype(bool))),
        "tech_free" : list(zip(frame["step"], frame["tech_free"].astype(bool))),
    }

    m1_one_mode = mtl.parse(
        "G[0,201] ("
        "(m1_busy & ~m1_down & ~m1_idle & ~m1_repair) "
        "| (~m1_busy & m1_down & ~m1_idle & ~m1_repair)"
        "| (~m1_busy & ~m1_down & m1_idle & ~m1_repair) "
        "| (~m1_busy & ~m1_down & ~m1_idle & m1_repair)"
        ")"
    )

    m2_one_mode = mtl.parse(
        "G[0,201] ("
        "(m2_busy & ~m2_down & ~m2_idle & ~m2_repair) "
        "| (~m2_busy & m2_down & ~m2_idle & ~m2_repair)"
        "| (~m2_busy & ~m2_down & m2_idle & ~m2_repair) "
        "| (~m2_busy & ~m2_down & ~m2_idle & m2_repair)"
        ")"
    )

    #XOR?
    max_one_part = mtl.parse(
        "G[0,201] ("
        "(idle & ~p_in & ~p_m1 & ~p_m2 & ~p_out) | "
        "(~idle & p_in & ~p_m1 & ~p_m2 & ~p_out) | "
        "(~idle & ~p_in & p_m1 & ~p_m2 & ~p_out) | "
        "(~idle & ~p_in & ~p_m1 & p_m2 & ~p_out) | "
        "(~idle & ~p_in & ~p_m1 & ~p_m2 & p_out)"
        ")"
    )

    not_both_in_repair = mtl.parse(
        "G[0,201] (~(m1_repair & m2_repair))"
    )

    part_at_m1_mode = mtl.parse(
        "G[0,201] (p_m1 -> ((m1_busy | m1_down | m1_repair) & ~(m1_idle)))"
    )

    machines_not_both_holding = mtl.parse(
        "G[0,201] (p_m1 -> ~(p_m2))"
    )

    #not pm2 should hold until pm1 =true
    m1_before_m2 = mtl.parse(
        "G[0,201] (p_in -> (~p_m2 W p_m1))"
    )

    eventually_shipped = mtl.parse("F[0,201] p_out")

    wait_may_continue = mtl.parse(
        "G[0,200] ("
        "((p_out & X ~(p_out)) & X idle) -> " #pout and next not pout so idle start
        "X (idle W p_in)" #until p_in comes idle goes on however p_in might not come
        ")"
    )


    results = {
        "trace": filename,
        "m1_one_mode": m1_one_mode(trace, time=0, quantitative=False, dt=1),
        "m2_one_mode": m2_one_mode(trace, time=0, quantitative=False, dt=1),
        "max_one_part": max_one_part(trace, time=0, quantitative=False, dt=1),
        "not_both_in_repair": not_both_in_repair(trace, time=0, quantitative=False, dt=1),
        "part_at_m1_mode": part_at_m1_mode(trace, time=0, quantitative=False, dt=1),
        "machines_not_both_holding": machines_not_both_holding(trace, time=0, quantitative=False, dt=1),
        "m1_before_m2": m1_before_m2(trace, time=0, quantitative=False, dt=1),
        "eventually_shipped": eventually_shipped(trace, time=0, quantitative=False, dt=1),
        "wait_may_continue": wait_may_continue(trace, time=0, quantitative=False, dt=1),
    }

    all_results.append(results)


output = pd.DataFrame(all_results)
#print(output)

for column in output.columns:
    if column != "trace":
        output[column] = output[column].map(
            lambda value: str(value).lower()
        )

output.to_csv(
    "results/production_system_ltl.csv",
    index=False
)