"""Test"""
import xml.etree.ElementTree as ET
from urllib.parse import unquote
import base64
import zlib
import re

IGNORE = ['id', 'label', 'placeholders', 'class_name']
"""Properties to ignore when parsing."""

class Node:
	"""Identifies a node object, as found in drawio.
	On one hand used for the individual components,
	but on the other hand used as a "group" of multiple
	nodes.
	"""
	def __init__(self, id, class_name, properties):
		self.id = id
		self.class_name = class_name
		self.properties = properties
		self._connections = {}
		self._inputs = set()
		self._outputs = set()
		self.children = []

	def __contains__(self, item):
		return item in self._inputs or item in self._outputs

	def __getitem__(self, item):
		return self.properties[item]

	def add_input(self, name):
		self._inputs.add(name)

	def add_output(self, name):
		self._outputs.add(name)

	def get_inputs(self):
		return list(self._inputs)

	def get_outputs(self):
		return list(self._outputs)

	def get_connections(self):
		return self._connections

	def add_connection(self, source, target):
		if source in self._connections:
			self._connections[source].append(target)
		else:
			self._connections[source] = [target]

	def get_properties_string(self, ignore=[]):
		res = ""
		for s in [f"{k}=({v if len(v) > 0 else 'None'})" for k, v in self.properties.items() if k not in IGNORE + ignore and '-' not in k]:
			res += ", " + s
		return res

	def is_empty(self):
		return len(self.children) == 0


class Page:
	"""A single page in drawio. Contains multiple nodes."""
	def __init__(self, name):
		self.name = name
		self.__nodes = []
		self.__imports = []

	def add_import(self, im, obj=None):
		self.__imports.append((im, obj))

	def add_node(self, node):
		if node is not None:
			self.__nodes.append(node)

	def get_imports(self):
		return self.__imports

	def get_nodes(self):
		return self.__nodes

	def get_sanitized_name(self):
		if re.match(r"Page-\d+", self.name):
			return self.name[len("Page-"):]
		return re.sub(r"[^a-zA-Z0-9_]", "", self.name)


class ParseException(Exception):
	"""Semantic exceptions when parsing."""
	def __init__(self, message):
		super().__init__(message)


class Parser:
	"""The drawio parser."""
	def __init__(self, filename, setup, ignore_empty_nodes=False):
		self.filename = filename
		self.input_class = setup["input class"]
		self.output_class = setup["output class"]
		self.class_object_path = setup["class object xpath"]
		self.special_object_path = setup["special object xpath"]
		self.verify = setup["verify"]
		self.ignore_empty_nodes = ignore_empty_nodes
		self.pages = []

		self.__class_names = {}

	@staticmethod
	def decode_and_deflate(data):
		"""Draw.io compresses each page as follows:
		First, all data is url-encoded
		Next, it is compressed/deflated
		Finally, it is encoded according to base64.

		To obtain the page data, we have to do the reverse.

		Returns:
			Uncompressed and decoded data as a string.
		"""
		decoded_data = base64.b64decode(data)
		inflated = zlib.decompress(decoded_data, -15).decode('utf-8')
		url_decoded_data = unquote(inflated)
		return ET.fromstring(url_decoded_data)

	def parse_page(self, page, nroot):
		"""Parses a single page of the model."""
		objects = nroot.findall(self.class_object_path)
		for obj in objects:
			page.add_node(self.create_node(nroot, obj.attrib, page))
		special = nroot.findall(self.special_object_path)
		for obj in special:
			if obj.attrib["role"] == "import":
				module = obj.attrib["module"]
				if "objects" in obj.attrib:
					objects = obj.attrib["objects"]
					page.add_import(module, objects)
				else:
					page.add_import(module)
		self.pages.append(page)

	def parse(self):
		"""Does the actual file parsing.

		If the file is compressed, we uncompress and work from there.
		If it wasn't compressed, we can work with the whole tree.

		Returns:
		 	A list of Node objects, representing the drawio file.
		"""
		tree = ET.parse(self.filename)
		root = tree.getroot()
		compressed = len(root.findall(".//mxGraphModel")) == 0
		pages = root.findall(".//diagram")
		for page in pages:
			page_obj = Page(page.attrib["name"])
			if compressed:
				nroot = self.decode_and_deflate(page.text)
			else:
				nroot = page
			self.parse_page(page_obj, nroot)
		self.verify(self.pages)

	def create_node(self, root, attr, page):
		class_name = attr["class_name"]
		# detect duplicate class names
		if class_name in self.__class_names:
			raise ParseException(f"In page {page.name}: duplicate definition of class '{class_name}'. "
			                     f"First defined in page {self.__class_names[class_name].name}.")
		# detect spaces in class names
		if re.search(r"\s", class_name) is not None:
			raise ParseException(f"In page {page.name}: invalid class '{class_name}'. Class names may not contain spaces.")

		node = Node(attr["id"], class_name, attr)
		self.__class_names[class_name] = page

		# Find the children of the node
		_rect = root.findall(".//*[@parent='%s']" % node.id)[1]
		components = root.findall(".//object/mxCell[@parent='%s']/.." % _rect.attrib["id"])

		lookup = {}

		for com in components:
			att = com.attrib
			if att["class_name"] in [self.input_class, self.output_class]:
				# Create the ports
				name = att["name"]
				# Duplicate ports are allowed for clarity in the model.
				# They map onto the same port!
				if att["class_name"] == self.input_class:
					node.add_input(name)
				else:
					node.add_output(name)
			else:
				# Normal Node
				child = Node(att["id"], att["class_name"], att)
				lookup[child.id] = child
				node.children.append(child)

		if self.ignore_empty_nodes and node.is_empty():
			return None

		edges = root.findall(".//*[@parent='%s'][@edge='1']" % _rect.attrib["id"])
		for edge in edges:
			att = edge.attrib
			source = root.find(".//*[@id='%s']" % att["source"])
			target = root.find(".//*[@id='%s']" % att["target"])
			# TODO: check for valid connection!
			if source.attrib["class_name"] == self.input_class:
				sblock = source.attrib["name"]
				spn = ""
			else:
				sblock = lookup[source[0].attrib["parent"]]
				spn = source.attrib["name"]
			if target.attrib["class_name"] == self.output_class:
				tblock = target.attrib["name"]
				tpn = ""
			else:
				tblock = lookup[target[0].attrib["parent"]]
				tpn = target.attrib["name"]
			# TODO: also allow attributes on edges?
			node.add_connection((sblock, spn), (tblock, tpn))

		return node


def parse_environment(vars):
	"""Parses the set of environment variables, given with the
	:code:`-E`/:code:`--environment` variable."""
	if vars is None:
		return {}
	sets = vars.split(",")
	return {k.strip(): v.strip() for k, v in [x.split("=") for x in sets]}
