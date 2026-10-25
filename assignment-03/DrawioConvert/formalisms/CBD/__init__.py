from src.parser import ParseException

def verify(pages):
	"""Check for unique block names per node."""
	for page in pages:
		for block in page.get_nodes():
			names = set()
			for node in block.children:
				bname = node["block_name"]
				if bname == "":
					bname = node["id"]
				if bname in names:
					raise ParseException(f"In page {page.name}: duplicate block name '{bname}' "
					                     f"in class '{block.class_name}'.")
				names.add(node["block_name"])

setup = {
	"parser": {
		"input class": "InputPort",
		"output class": "OutputPort",
		"verify": verify
	},
	"generator": {
		"ignore": ["__docstring__", "symbol", "block_name"],
		"environment": ["delta"],
		"templates": [
			{
				"template": "model.py.jinja",
				"pattern": "{prefix}{u}{page}.py",
				"multipage": True,
				"overwrite": True,
				"auto": True,
				"entry": False
			},
			{
				"template": "experiment.py.jinja",
				"pattern": "{prefix}_experiment.py",
				"multipage": False,
				"overwrite": False,
				"auto": True,
				"entry": True
			}
		]
	}
}
