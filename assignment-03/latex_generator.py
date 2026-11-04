from generated.OscillatorDerivative import OscillatorDerivative
from generated.OscillatorIntegral import OscillatorIntegral

from CBD.library import *
def latex_port(port):
    # full hierarchical path of the port
    name = port.getPath()

    # escp
    name = name.replace("_", r"\_")

    return r"\mathrm{" + name + "}"


def input_source(block, input_name):
    port = block.getInputPortByName(input_name)
    connection = port.getIncoming()

    if connection is None:
        raise ValueError(f"Input {input_name} is not connected")

    return connection.source


def integrator_equations(block):
    # integrator's output port
    output = latex_port(block.getOutputPortByName("OUT1"))

    # sources
    input_signal = latex_port(input_source(block, "IN1"))
    initial_condition = latex_port(input_source(block, "IC"))

    # continuous-time equations
    equations = [
        rf"\frac{{d}}{{dt}} {output}(t) = {input_signal}(t)",
        rf"{output}(0) = {initial_condition}(0)"
    ]

    return equations

def derivator_equations(block):
    output = latex_port(block.getOutputPortByName("OUT1"))

    input_signal = latex_port(input_source(block, "IN1"))

    initial_condition = latex_port(input_source(block, "IC"))

    equations = [
        rf"{output}(t) = \frac{{d}}{{dt}} {input_signal}(t)",
        rf"{output}(0) = {initial_condition}(0)"
    ]

    return equations

def constant_equation(block):
    output = latex_port(block.getOutputPortByName("OUT1"))

    value = block.getValue()

    return f"{output}(t) = {value}"

def negator_equation(block):
    output = latex_port(block.getOutputPortByName("OUT1"))

    input_signal = latex_port(input_source(block, "IN1"))

    return f"{output}(t) = -{input_signal}(t)"

def constant_equation(block):
    output = latex_port(block.getOutputPortByName("OUT1"))

    value = block.getValue()

    return f"{output}(t) = {value}"


def adder_equation(block):
    output = latex_port(block.getOutputPortByName("OUT1"))

    inputs = []

    for port in block.getInputPorts():
        source = input_source(block, port.name)
        inputs.append(latex_port(source) + "(t)")

    expression = " + ".join(inputs)

    return f"{output}(t) = {expression}"

def product_equation(block):
    output = latex_port(block.getOutputPortByName("OUT1"))

    inputs = []

    for port in block.getInputPorts():
        source = input_source(block, port.name)
        inputs.append(latex_port(source) + "(t)")

    expression = r" \cdot ".join(inputs)

    return f"{output}(t) = {expression}"

def inverter_equation(block):
    output = latex_port(block.getOutputPortByName("OUT1"))

    source = input_source(block, "IN1")
    input_signal = latex_port(source)

    return rf"{output}(t) = \frac{{1}}{{{input_signal}(t)}}"

def generic_equation(block):
    output = latex_port(block.getOutputPortByName("OUT1"))

    source = input_source(block, "IN1")
    input_signal = latex_port(source)

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
        raise NotImplementedError(
            f"unsupported: {operator}"
        )

    latex_operator = latex_operators[operator]

    if operator == "sqrt":
        expression = rf"\sqrt{{{input_signal}(t)}}"
    else:
        expression = rf"{latex_operator}\left({input_signal}(t)\right)"

    return f"{output}(t) = {expression}"

def time_equations(block):
    equations = []

    for port in block.getOutputPorts():
        output = latex_port(port)
        equations.append(f"{output}(t) = t")

    return equations

def delay_equations(block):
    output = latex_port(block.getOutputPortByName("OUT1"))
    source = latex_port(input_source(block, "IN1"))
    ic = latex_port(input_source(block, "IC"))

    return [
        f"{output}(0) = {ic}(0)",
        rf"{output}(t) = {source}(t-\Delta t), \quad t=n\Delta t,\ n\geq1"
    ]

def generate_ct_equations(model):
    equations = []

    for block in model.getBlocks():

        if isinstance(block, IntegratorBlock):
            equations.extend(integrator_equations(block))

        elif isinstance(block, DerivatorBlock):
            equations.extend(derivator_equations(block))

        elif isinstance(block, NegatorBlock):
            equations.append(negator_equation(block))

        elif isinstance(block, ConstantBlock):
            equations.append(constant_equation(block))

        elif isinstance(block, AdderBlock):
            equations.append(adder_equation(block))

        elif isinstance(block, ProductBlock):
            equations.append(product_equation(block))

        elif isinstance(block, InverterBlock):
            equations.append(inverter_equation(block))

        elif isinstance(block, GenericBlock):
            equations.append(generic_equation(block))

        elif isinstance(block, TimeBlock):
            equations.extend(time_equations(block))

        elif isinstance(block, DelayBlock):
            equations.extend(delay_equations(block))

        elif isinstance(block, DeltaTBlock):
            continue

        else:
            raise NotImplementedError(
                f"unsupported block: {block.getPath()}"
            )

    return equations

# ai assistance was used to improve latex formatting in
# format_ct_latex() and save_ct_document().

def format_ct_latex(equations):
    lines = []

    for equation in equations:
        lines.append(equation.replace(" = ", " &= ", 1))

    return (
        "\\[\n"
        "\\begin{aligned}\n"
        + " \\\\[4pt]\n".join(lines)
        + "\n\\end{aligned}\n"
        "\\]"
    )

from pathlib import Path

def save_ct_document(model):
    equations = generate_ct_equations(model)
    latex = format_ct_latex(equations)

    document = (
        "\\documentclass{article}\n"
        "\\usepackage{amsmath}\n"
        "\\begin{document}\n"
        + latex +
        "\n\\end{document}"
    )

    Path("latex_output").mkdir(exist_ok=True)

    filename = Path("latex_output") / f"{model.getBlockName()}_ct.tex"
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

        equations = generate_ct_equations(model)

        for equation in equations:
            print(equation)

        filename = save_ct_document(model)
        print(f"Generated: {filename}")
