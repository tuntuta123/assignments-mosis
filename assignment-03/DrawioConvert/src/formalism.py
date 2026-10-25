"""This module contains the Formalism class, which contains and loads the basic formalism information."""
from src.parser import ParseException
import os

class Formalism:
	"""Contains and loads the basic formalism information.

	Args:
		logger (Logger):    The logger to use.
		here (str):         The location of :code:`DrawioConvert`.
		args:               Parsed arguments from the :class:`ArgumentParser`
	"""
	def __init__(self, logger, here, args):
		self.formalism = args.formalism
		self.logger = logger
		self.here = here

	@staticmethod
	def defaults():
		"""The default setup values."""
		default_setup_parser = {
			"input class": "InputPort",
			"output class": "OutputPort",
			"class object xpath": ".//object/mxCell/mxGeometry/mxRectangle/../../..[@class_name]",
			"special object xpath": ".//object/mxCell/mxGeometry/../..[@role]",
			"verify": lambda x: x
		}

		default_setup_generator = {
			"ignore": [],
			"environment": [],
			"templates": []
		}

		return default_setup_parser, default_setup_generator

	def load_formalism(self):
		"""Loads the formalism's setup variable."""
		self.logger.debug("Loading Formalism...")
		with open(os.path.join(self.here, "formalisms", self.formalism, "__init__.py"), 'r') as file:
			_locals = {}
			exec(file.read(), globals(), _locals)
			setup = _locals["setup"]

			default_setup_parser, default_setup_generator = self.defaults()

			setup_parser = setup.get("parser", {})
			setup_parser = {**default_setup_parser, **setup_parser}

			setup_generator = setup.get("generator", {})
			setup_generator = {**default_setup_generator, **setup_generator}
		self.logger.debug("Loaded Formalism.")
		return setup_parser, setup_generator

	def valid_formalism(self):
		"""Checks if the formalism exists."""
		contents = os.listdir(os.path.join(self.here, "formalisms"))
		return self.formalism in contents
