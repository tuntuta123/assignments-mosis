from src.formalism import Formalism
from src.generator import Generator
from src.parser import Parser
from src.logger import Logger
import argparse
import sys
import os

_here = os.path.dirname(os.path.realpath(__file__))


class ListFormalisms(argparse.Action):
	def __init__(self, option_strings,
	             dest=argparse.SUPPRESS,
	             default=argparse.SUPPRESS, **kwargs):
		super().__init__(
			option_strings=option_strings,
			dest=dest,
			default=default,
			nargs=0,
			**kwargs)

	def __call__(self, parser, namespace, values, option_string=None):
		print("The following formalisms are available for generation "
		      "('ENV' identifies which environment variables are available):")
		self.list()
		print("\nUse the -F/--formalism flag to specify which one you want to use.")
		parser.exit()

	@staticmethod
	def list():
		contents = os.listdir(os.path.join(_here, "formalisms"))
		for file in contents:
			path = os.path.join(_here, "formalisms", file)
			if os.path.isdir(path) and "__init__.py" in os.listdir(path):
				_local = {}
				with open(os.path.join(path, "__init__.py")) as F:
					exec(F.read(), {}, _local)
				print("  -", "{:<10}".format(file), "ENV:", _local["setup"]["generator"]["environment"])


# Read commandline variables
argprs = argparse.ArgumentParser(description='Create model/simulation files from draw.io/diagrams.net XML files.')
argprs.add_argument('input', type=str, help="The input file to convert.")
argprs.add_argument("-F", "--formalism", required=True,
                    help="The formalism for which files must be generated. "
                         "Use -L or --list to show the available formalisms.")
argprs.add_argument("-e", "--entry", default='', help="The topmost class to use in the simulation.")
argprs.add_argument("-t", "--time", default=10, type=float, help="Total simulation time. (default: 10)")
argprs.add_argument('-L', '--list', action=ListFormalisms, help="Lists the available formalisms.")
argprs.add_argument('-s', '--skip', action='store_true',
                    help="When set, empty blocks will be skipped in the generation, otherwise they are created.")
argprs.add_argument('-d', '--directory', default='./',
                    help="Directory of where the files must be generated. (default: ./)")
argprs.add_argument('-f', '--force', action='store_true', help="Force generation of the experiment file.")
argprs.add_argument('-a', '--all', action='store_true', help="Generate all files associated to the formalism.")
argprs.add_argument('-S', '--singlefile', action='store_true',
                    help="Ignore the page separations and only generate a single file.")
argprs.add_argument('-r', '--reversed', action='store_true', help="Generate the drawio page files in reverse order.")
argprs.add_argument('-g', '--globalimports', action='store_true',
                    help="When set, the imports listed in drawio will be page-independent.")
argprs.add_argument('-v', '--verbose', action='store_true', help="Output generation information.")
argprs.add_argument('-E', '--environment', help="Optional parameters to add to the generation; "
                                                "as comma-separated key-value list. See -L/--list for more info.")
args = argprs.parse_args()

logger = Logger(args.verbose)
form = Formalism(logger, _here, args)
if not form.valid_formalism():
	logger.error(f"Could not find formalism '{form.formalism}'. Try one of:")
	ListFormalisms.list()
	sys.exit(1)
try:
	setup_parser, setup_generator = form.load_formalism()
except Exception as e:
	logger.error("Could not load formalism.", e)
	sys.exit(1)


parser = Parser(args.input, setup_parser, args.skip)
parser.parse()
gen = Generator(logger, _here, args)
gen.generate_files(setup_generator, parser.pages)
