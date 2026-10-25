from src.parser import parse_environment
from jinja2 import Template
import sys
import os


class Generator:
	"""Generates the files from the internal data structure."""
	def __init__(self, logger, here, args):
		self.logger = logger
		self.here = here
		self.args = args

	def generate_file(self, loc, blueprint, **fields):
		if os.path.isfile(loc) and not blueprint.get("overwrite", True) and not self.args.force:
			self.logger.warning(f"File '{loc}' already exists. Use -f/--force to regenerate this file.")
			return
		path = os.path.join(self.here, "formalisms", self.args.formalism, blueprint["template"])
		with open(path, 'r') as file:
			template = Template(file.read(), trim_blocks=True, lstrip_blocks=True)
		env = parse_environment(self.args.environment)
		contents = template.render(entry=self.args.entry, **fields, **env)
		with open(loc, 'w') as file:
			file.write(contents)
		self.logger.debug(f"Generated '{loc}'.")

	def generate_files(self, setup_generator, pages):
		prefix = os.path.basename(self.args.input)
		prefix = prefix[:prefix.find(".")]
		fields = {
			"command": " ".join(sys.argv),
			"ignore": setup_generator["ignore"],
			"time": self.args.time
		}
		generated_files = []
		imports = []
		if self.args.globalimports:
			for page in pages:
				imports += page.get_imports()
		if self.args.reversed:
			pages = list(reversed(pages))
		for blueprint in setup_generator["templates"]:
			if blueprint.get("auto", True) or self.args.all:
				if blueprint.get("entry", False):
					if self.args.entry == '':
						self.logger.warning(f"Could not generate file(s). -e/--entry missing.")
						continue
				if blueprint.get("multipage", True) and not self.args.singlefile:
					for page in pages:
						pname = page.get_sanitized_name()
						u = "_"
						if len(pages) == 1:
							pname = ""
							u = ""
						fname = blueprint["pattern"].format(prefix=prefix, page=pname, u=u)
						loc = os.path.join(self.args.directory, fname)
						if not self.args.globalimports:
							imports = page.get_imports()
						self.generate_file(loc, blueprint, **fields, imports=imports, nodes=page.get_nodes(),
						                   files=generated_files)
						generated_files.append(fname)
				else:
					fname = blueprint["pattern"].format(prefix=prefix, page="", u="")
					loc = os.path.join(self.args.directory, fname)
					a = {
						"imports": [],
						"nodes": []
					}
					for page in pages:
						a["imports"] += page.get_imports()
						a["nodes"] += page.get_nodes()
					self.generate_file(loc, blueprint, **fields, **a, files=generated_files)
					generated_files.append(fname)
		self.logger.debug("Done.")

