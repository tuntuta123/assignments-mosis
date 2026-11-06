from CBD.simulator import *
from dt_latex_generator import *


def collect_blocks(model):
    blocks = []

    for block in model.getBlocks():

        if isinstance(block, (IntegratorBlock, DerivatorBlock)):
            blocks.append(block)

        elif isinstance(block, CBD):
            blocks.extend(collect_blocks(block))

        elif isinstance(block, ScopeBlock):
            continue

        else:
            blocks.append(block)

    return blocks


def producer(port, blocks):
    # walk through the ports of plain cbds until a block we write an equation for
    connection = port.getIncoming()

    while connection is not None:
        source = connection.source

        if source.block in blocks:
            return source.block

        connection = source.getIncoming()

    return None


def read_inputs(block):
    # inputs read at the same index i (or at 0), values from i-1 come from history
    if isinstance(block, DelayBlock):
        return ["IC"]

    if isinstance(block, IntegratorBlock):
        return ["IC"]

    if isinstance(block, DerivatorBlock):
        return ["IN1", "IC", "DT"]

    return block.getInputPortNames()


def build_dependency_graph(model):
    # one graph for i = 0 and i >= 1 together, so the order is valid for both
    blocks = collect_blocks(model)
    graph = DependencyGraph()

    for block in blocks:
        graph.addNode(block)

    for block in blocks:
        for name in read_inputs(block):
            source = producer(block.getInputPortByName(name), blocks)

            if source is not None:
                graph.addDependency(block, source)

    return graph


def block_equations(block):
    if isinstance(block, IntegratorBlock):
        return integrator_equations(block)

    elif isinstance(block, DerivatorBlock):
        return derivator_equations(block)

    elif isinstance(block, ConstantBlock):
        return [constant_equation(block)]

    elif isinstance(block, AdderBlock):
        return [adder_equation(block)]

    elif isinstance(block, NegatorBlock):
        return [negator_equation(block)]

    elif isinstance(block, ProductBlock):
        return [product_equation(block)]

    elif isinstance(block, InverterBlock):
        return [inverter_equation(block)]

    elif isinstance(block, GenericBlock):
        return [generic_equation(block)]

    elif isinstance(block, TimeBlock):
        return time_equations(block)

    elif isinstance(block, DeltaTBlock):
        return [delta_t_equation(block)]

    elif isinstance(block, DelayBlock):
        return delay_equations(block)

    raise NotImplementedError(f"Unsupported block: {block.getPath()}")


def generate_sorted_equations(model):
    # list of groups in computation order
    # a group with one block is a normal step, a group with more is an algebraic loop
    graph = build_dependency_graph(model)
    components = strongly_connected_components(graph)
    ordered = topological_sort(graph, components)

    groups = []

    for component in ordered:
        equations = []

        for block in component:
            equations.extend(block_equations(block))

        groups.append({
            "loop": is_algebraic_loop(component, graph),
            "equations": equations,
        })

    return groups


# ai assistance was used to improve latex formatting in
# format_sorted_latex() and save_sorted_document().

def array_row(equation):
    # every left side gets the same width, so the "=" line up in all groups
    lhs, rhs = equation.split(" = ", 1)
    return f"\\makebox[\\lhswidth][r]{{${lhs}$}} & = & {rhs}"


def inner_array(equations):
    rows = " \\\\\n".join(array_row(eq) for eq in equations)
    return "\\begin{array}{rcl}\n" + rows + "\n\\end{array}"


def format_sorted_latex(groups):
    # outer array: first column holds the brace of a loop, second the equations
    rows = []
    run = []

    for group in groups:

        if group["loop"]:
            if run:
                rows.append(" & " + inner_array(run))
                run = []

            equations = inner_array(group["equations"])
            rows.append(
                "\\left\\{\\vphantom{" + equations + "}\\right. & "
                + equations
            )

        else:
            run.extend(group["equations"])

    if run:
        rows.append(" & " + inner_array(run))

    # widest left side, measured by latex itself
    left_sides = [
        eq.split(" = ", 1)[0]
        for group in groups
        for eq in group["equations"]
    ]
    measure = " \\\\ ".join(left_sides)

    return (
            "\\newlength{\\lhswidth}\n"
            "\\settowidth{\\lhswidth}{$\\begin{array}{@{}r@{}}"
            + measure +
            "\\end{array}$}\n"
            "\\[\n"
            "\\resizebox{\\textwidth}{!}{$"
            "\\begin{array}{@{}l@{}l@{}}\n"
            + " \\\\\n".join(rows) +
            "\n\\end{array}"
            "$}\n"
            "\\]"
    )


def save_sorted_document(model):
    groups = generate_sorted_equations(model)
    latex = format_sorted_latex(groups)

    document = (
            "\\documentclass{article}\n"
            "\\usepackage{amsmath}\n"
            "\\usepackage{graphicx}\n"
            "\\begin{document}\n"
            + latex +
            "\n\\end{document}\n"
    )

    Path("latex_output").mkdir(exist_ok=True)

    filename = Path("latex_output") / f"{model.getBlockName()}_sorted.tex"
    filename.write_text(document, encoding="utf-8")

    return filename


if __name__ == "__main__":
    from generated.CBD_equation_1 import CBD_equation_1
    from generated.CBD_equation_2 import CBD_equation_2
    from generated.CBD_equation_3 import CBD_equation_3
    from generated.OscillatorIntegral import OscillatorIntegral
    from generated.OscillatorDerivative import OscillatorDerivative

    models = [
        CBD_equation_1("Model1"),
        CBD_equation_2("Model2"),
        CBD_equation_3("Model3"),
        OscillatorIntegral("Integral"),
        OscillatorDerivative("Derivative")
    ]

    for model in models:
        print(f"\nModel: {model.getBlockName()}")

        for group in generate_sorted_equations(model):
            if group["loop"]:
                print("algebraic loop:")
                for equation in group["equations"]:
                    print("  ", equation)
            else:
                for equation in group["equations"]:
                    print(equation)

        filename = save_sorted_document(model)
        print(f"Generated: {filename}")
