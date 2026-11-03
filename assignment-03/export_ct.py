from generated.CBD_equation_1 import CBD_equation_1
from generated.CBD_equation_2 import CBD_equation_2
from generated.CBD_equation_3 import CBD_equation_3

from generated.OscillatorIntegral import OscillatorIntegral
from generated.OscillatorDerivative import OscillatorDerivative

from latex_generator import save_ct_document


models = [
    CBD_equation_1("Model1"),
    CBD_equation_2("Model2"),
    CBD_equation_3("Model3"),
    OscillatorIntegral("Integral"),
    OscillatorDerivative("Derivative")
]

for model in models:
    filename = save_ct_document(model)

    print(f"Generated: {filename}")
