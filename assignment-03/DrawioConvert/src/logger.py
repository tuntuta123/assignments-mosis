"""Helper class to allow for simplistic logging of info."""

class Logger:
	def __init__(self, verbose):
		self.verbose = verbose

	def debug(self, message):
		if self.verbose:
			print("[  DEBUG  ]", message)

	def warning(self, message):
		print("[ WARNING ]", message)

	def error(self, message, error=None):
		print("[  ERROR  ]", message)
		if error:
			print(error)
