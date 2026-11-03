from generated.CBD_equation_1 import CBD_equation_1
from generated.CBD_equation_2 import CBD_equation_2

from latex_generator import generate_ct_equations


models = [
    CBD_equation_1("Model1"),
    CBD_equation_2("Model2")
]

for model in models:
    print(f"\nModel: {model.getBlockName()}")

    equations = generate_ct_equations(model)

    for equation in equations:
        print(equation)