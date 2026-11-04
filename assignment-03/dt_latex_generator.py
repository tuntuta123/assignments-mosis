
from pathlib import Path

from generated.OscillatorDerivative import OscillatorDerivative
from generated.OscillatorIntegral import OscillatorIntegral

from CBD.model import CBD
from CBD.library import *


def dt_signal(port, index="i"):
    name = port.getPath().replace("_", r"\_")
    return rf"\mathrm{{{name}}}({index})"


def input_source(block, input_name):
    port = block.getInputPortByName(input_name)
    connection = port.getIncoming()

    if connection is None:
        raise ValueError(f"Input {input_name} is not connected")

    return connection.source


def constant_equation(block):
    output = dt_signal(block.getOutputPortByName("OUT1"))
    value = block.getValue()

    return f"{output} = {value}"


def adder_equation(block):
    output = dt_signal(block.getOutputPortByName("OUT1"))

    inputs = []
    for port in block.getInputPorts():
        source = input_source(block, port.name)
        inputs.append(dt_signal(source))

    expression = " + ".join(inputs)

    return f"{output} = {expression}"


def negator_equation(block):
    output = dt_signal(block.getOutputPortByName("OUT1"))
    source = dt_signal(input_source(block, "IN1"))

    return f"{output} = -{source}"


def product_equation(block):
    output = dt_signal(block.getOutputPortByName("OUT1"))

    inputs = []
    for port in block.getInputPorts():
        source = input_source(block, port.name)
        inputs.append(dt_signal(source))

    expression = r" \cdot ".join(inputs)

    return f"{output} = {expression}"


def inverter_equation(block):
    output = dt_signal(block.getOutputPortByName("OUT1"))
    source = dt_signal(input_source(block, "IN1"))

    return rf"{output} = \frac{{1}}{{{source}}}"


def generic_equation(block):
    output = dt_signal(block.getOutputPortByName("OUT1"))
    source = dt_signal(input_source(block, "IN1"))

    operator = block.getBlockOperator()

    latex_operators = {
        "sin": r"\sin",
        "cos": r"\cos",
        "tan": r"\tan",
        "exp": r"\exp",
        "log": r"\log",
        "sqrt": r"\sqrt"
    }

    if operator not in latex_operators:
        raise NotImplementedError(f"Unsupported operator: {operator}")

    latex_operator = latex_operators[operator]

    if operator == "sqrt":
        expression = rf"\sqrt{{{source}}}"
    else:
        expression = rf"{latex_operator}\left({source}\right)"

    return f"{output} = {expression}"


def time_equations(block):
    equations = []

    for port in block.getOutputPorts():
        output = dt_signal(port)
        equations.append(rf"{output} = i\Delta t")

    return equations


def delta_t_equation(block):
    output = dt_signal(block.getOutputPortByName("OUT1"))

    return rf"{output} = \Delta t"


def delay_equations(block):
    output = block.getOutputPortByName("OUT1")

    source = input_source(block, "IN1")
    ic = input_source(block, "IC")

    return [
        f"{dt_signal(output, '0')} = {dt_signal(ic, '0')}",
        rf"{dt_signal(output)} = {dt_signal(source, 'i-1')}, \quad i \geq 1"
    ]


def integrator_equations(block):
    output = block.getOutputPortByName("OUT1")

    source = input_source(block, "IN1")
    ic = input_source(block, "IC")
    dt = input_source(block, "DT")

    #generate with forward euler
    return [
        f"{dt_signal(output, '0')} = {dt_signal(ic, '0')}",
        (
            f"{dt_signal(output)} = {dt_signal(output, 'i-1')}"
            rf" + {dt_signal(dt, 'i-1')} \cdot {dt_signal(source, 'i-1')},"
            r" \quad i \geq 1"
        )
    ]


def derivator_equations(block):
    output = block.getOutputPortByName("OUT1")

    source = input_source(block, "IN1")
    ic = input_source(block, "IC")
    dt = input_source(block, "DT")

    current = dt_signal(source)
    previous = dt_signal(source, "i-1")
    step = dt_signal(dt)

    return [
        f"{dt_signal(output, '0')} = {dt_signal(ic, '0')}",
        (
            rf"{dt_signal(output)} = "
            rf"\frac{{{current} - {previous}}}{{{step}}},"
            r" \quad i \geq 1"
        )
    ]


def generate_dt_equations(model):
    equations = []

    for block in model.getBlocks():

        if isinstance(block, IntegratorBlock):
            equations.extend(integrator_equations(block))

        elif isinstance(block, DerivatorBlock):
            equations.extend(derivator_equations(block))

        elif isinstance(block, CBD):
            equations.extend(generate_dt_equations(block))

        elif isinstance(block, ConstantBlock):
            equations.append(constant_equation(block))

        elif isinstance(block, AdderBlock):
            equations.append(adder_equation(block))

        elif isinstance(block, NegatorBlock):
            equations.append(negator_equation(block))

        elif isinstance(block, ProductBlock):
            equations.append(product_equation(block))

        elif isinstance(block, InverterBlock):
            equations.append(inverter_equation(block))

        elif isinstance(block, GenericBlock):
            equations.append(generic_equation(block))

        elif isinstance(block, TimeBlock):
            equations.extend(time_equations(block))

        elif isinstance(block, DeltaTBlock):
            equations.append(delta_t_equation(block))

        elif isinstance(block, DelayBlock):
            equations.extend(delay_equations(block))

        elif isinstance(block, ScopeBlock):
            continue

        else:
            raise NotImplementedError(
                f"Unsupported block: {block.getPath()}"
            )

    return equations

# ai assistance was used to improve latex formatting in
# format_dt_latex() and save_dt_document().

def format_dt_latex(equations):
    lines = []

    for equation in equations:
        lines.append(equation.replace(" = ", " & = & ", 1))

    body = r" \\ ".join(lines)

    return (
        "\\begin{center}\n"
        "\\resizebox{\\textwidth}{!}{$"
        "\\left\\{\\begin{array}{rcl}"
        + body +
        "\\end{array}\\right."
        "$}\n"
        "\\end{center}"
    )


def save_dt_document(model):
    equations = generate_dt_equations(model)
    latex = format_dt_latex(equations)

    document = (
        "\\documentclass{article}\n"
        "\\usepackage{amsmath}\n"
        "\\usepackage{graphicx}\n"
        "\\begin{document}\n"
        + latex +
        "\n\\end{document}\n"
    )

    Path("latex_output").mkdir(exist_ok=True)

    filename = Path("latex_output") / f"{model.getBlockName()}_dt.tex"
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

        equations = generate_dt_equations(model)

        for equation in equations:
            print(equation)

        filename = save_dt_document(model)
        print(f"Generated: {filename}")
