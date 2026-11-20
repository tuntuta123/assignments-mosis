#!/usr/bin/env python3
"""
	Simple script for generating a Reachability or a Coverability Graph from a TAPAAL
	Petri-Net (https://www.tapaal.net/). Additionally, it is possible to generate the
	P-Invariant formulas for the given net. The net must not be a Game Net or a Timed
	Net. It is allowed to contain inhibitor and/or weighted arcs. Note that the net
	should not yield any errors in TAPAAL for this script to work.

	The graphs are written in GraphViz format, which can be converted to an image or
	viewed in xdot, GraphDonkey or any other GraphViz viewer. Large graphs (over 1000
	nodes) might not be displayable due to their size. In general, the LTL/CTL languages
	are used for Petri-Net analysis. This script is therefore purely meant for educational
	purposes, hence the limited node size should not be a problem.

	Usage (any unambiguous prefix of a command works, e.g. "./RC.py c net.tapn"):
		./RC.py reachability net.tapn [-o rg.dot] [--table rg.csv] [--limit N]
		./RC.py coverability net.tapn [-o cg.dot] [--table cg.csv] [--limit N]
		./RC.py invariants   net.tapn
		./RC.py net          net.tapn [-o net.dot]

	Graphs go to the console unless -o is given; messages and warnings go to stderr,
	so "./RC.py c net.tapn | dot -Tpng -o cg.png" works. Run a command with -h for
	all of its options.
"""

import xml.etree.ElementTree as ET
import math
import sys


def log(message):
	print(message, file=sys.stderr)

def gcd(collection):
	r = 0
	for c in collection:
		r = math.gcd(r, c)
	return r

NAMESPACE = 'http://www.informatik.hu-berlin.de/top/pnml/ptNetb'  # The namespace of the *.tapn XML
nm = lambda n: '{%s}%s' % (NAMESPACE, n)                          # Automatically applies the namespace

OMEGA = u"\u03C9"   # The omega symbol

class PetriNet:
	"""
	Simple Petri-Net class.

	Args:
		fname (str):	The name of the *.tapn file, which contains the Petri-Net.

	Raises:
		TypeError if the net is not a P/T net, or when it is a Game Net or a Timed Net.
	"""
	def __init__(self, fname):
		self.places = {}       # The set of places:   {ID -> [name, marking]}
		self.transitions = {}  # The transitions:     {ID -> name}
		self.arcs = {}         # The arcs:            {ID -> (source, target, isInhibitor, weight)}
		self._sa = {}          # The source-arc link: {SourceID -> ArcID*}
		self._ta = {}          # The target-arc link: {TargetID -> ArcID*}
		self._mvec = []        # The ordered marking vector; all place IDs
		self._vars = {}        # The variables that can be used as weights in a net
		self._shared = set()   # A dictionary of all shared places

		tree = ET.parse(fname)
		root = tree.getroot()

		duplicates = {}

		# Check validity
		fts = root.find(nm('feature')).attrib
		for feature in ('isGame', 'isTimed', 'isColored', 'isStochastic'):
			if fts.get(feature, "false") != "false":
				raise TypeError("Invalid Net: %s nets are not supported" % feature[2:].lower())

		# Obtain all constants
		for var in root.iter(nm('constant')):
			attr = var.attrib
			self._vars[attr['name']] = float(attr['value'])

		# Obtain all shared places
		# Shared places do not get a prefix
		# This prevents name collisions
		for place in root.iter(nm('shared-place')):
			attr = place.attrib
			id = attr['name']
			self._shared.add(id)
			self.places[id] = [id, int(attr['initialMarking'])]
			self._mvec.append(id)

		for net in root.iter(nm('net')):
			if net.attrib['type'] != "P/T net":
				raise TypeError("Invalid Net")

			net_id = net.attrib['id']

			# Prepend all ids and names with the net_id
			#  to prevent name collisions
			def get_name(name):
				if name in self._shared:
					return name
				return net_id + "." + name

			for place in net.iter(nm('place')):
				attr = place.attrib
				if attr['id'] in self._shared:
					continue
				id = get_name(attr['id'])
				self.places[id] = [get_name(attr['name']), int(attr['initialMarking'])]
				self._mvec.append(id)
			for trans in net.iter(nm('transition')):
				attr = trans.attrib
				id = get_name(attr['id'])
				self.transitions[id] = get_name(attr['name'])
			for arc in net.iter(nm('arc')):
				attr = arc.attrib
				id = get_name(attr['id'])
				if id in self.arcs:
					if id not in duplicates:
						duplicates[id] = 2
					else:
						duplicates[id] += 1
					id += "-" + str(duplicates[id])
				weight = int(self._vars.get(attr['weight'], attr['weight']))
				self.arcs[id] = (get_name(attr['source']), get_name(attr['target']), (attr['type'] == 'tapnInhibitor'), weight)
				self._sa.setdefault(get_name(attr['source']), []).append(id)
				self._ta.setdefault(get_name(attr['target']), []).append(id)
				if self.arcs[id][0] in self.places and self.arcs[id][1] in self.places:
					raise ValueError("Cannot connect place %s to place %s!" % (self.arcs[id][0], self.arcs[id][1]))
				if self.arcs[id][0] in self.transitions and self.arcs[id][1] in self.transitions:
					raise ValueError("Cannot connect transition %s to transition %s!" % (self.arcs[id][0], self.arcs[id][1]))
		self._mvec.sort()

	def setMarking(self, marking):
		"""
		Sets the current marking.

		Args:
			marking (iter):	The marking to set.
		"""
		for i, m in enumerate(marking):
			self.places[self._mvec[i]][1] = m

	def getMarking(self):
		"""
		Obtains the current marking.
		"""
		res = []
		for pid in self._mvec:
			res.append(self.places[pid][1])
		return res

	@staticmethod
	def toString(marking):
		"""
		Converts a marking to a string. This prevents the quotes around omegas.
		"""
		return "[%s]" % ", ".join([str(x) for x in marking])

	def canFire(self, trans):
		"""
		Checks if a transition can fire.

		Args:
			trans (str):	The transition's ID.
		"""
		for aid in self._ta.get(trans, []):
			source, _, inh, w = self.arcs[aid]
			tokens = self.places[source][1]
			if inh and PetriNet.intLTE(w, tokens):
				return False
			elif not inh and PetriNet.intLT(tokens, w):
				return False
		return True

	def fire(self, trans):
		"""
		Fires a transition if :func:`canFire` returned :code:`True`.
		Otherwise, an AssertionError is thrown.

		Args:
			trans (str):	The transition's ID.
		"""
		assert self.canFire(trans), "Cannot fire the transition"
		for aid in self._ta.get(trans, []):
			source, _, inh, w = self.arcs[aid]
			if not inh and type(self.places[source][1]) == int:
				self.places[source][1] -= w
		for aid in self._sa.get(trans, []):
			_, target, __, w = self.arcs[aid]
			if target not in self.places:
				log("WARNING: No such place %s reachable from %s. Please recreate both to make your model valid." % (target, trans))
				continue
			if type(self.places[target][1]) == int:
				self.places[target][1] += w

	def nextMarkings(self):
		"""
		Obtains a set of all transitions that can fire and connects
		them to the marking after they would have fired.
		"""
		initial = self.getMarking()[:]
		result = []
		for trans in self.transitions.keys():
			if self.canFire(trans):
				self.fire(trans)
				result.append((trans, self.getMarking()[:]))
				self.setMarking(initial)
		return result

	@staticmethod
	def markingLTE(M1, M2):
		"""
		Checks if M1 <= M2.

		Args:
			M1 (iter):	Marking 1
			M2 (iter):	Marking 2
		"""
		assert len(M1) == len(M2), "Can only compare markings of equal length"
		for i in range(len(M1)):
			if PetriNet.intLT(M2[i], M1[i]):
				return False
		return True

	@staticmethod
	def markingLTsome(M1, M2):
		"""
		Checks if there is at least some marking in M1 that is less than M2.

		Args:
			M1 (iter):	Marking 1
			M2 (iter):	Marking 2
		"""
		assert len(M1) == len(M2), "Can only compare markings of equal length"
		for i in range(len(M1)):
			if PetriNet.intLT(M1[i], M2[i]):
				return True
		return False

	@staticmethod
	def markingDominates(M1, M2):
		"""
		Checks if M1 dominates M2.

		Args:
			M1 (iter):	Marking 1
			M2 (iter):	Marking 2
		"""
		assert len(M1) == len(M2), "Can only compare markings of equal length"
		return PetriNet.markingLTE(M2, M1) and PetriNet.markingLTsome(M2, M1)

	@staticmethod
	def intLT(a, b):
		"""
		Checks if a < b, where :attr:`OMEGA` is larger than every integer.

		Args:
			a:	Either an integer, or :attr:`OMEGA`.
			b:	Either an integer, or :attr:`OMEGA`.
		"""
		if a == OMEGA:
			return False
		return b == OMEGA or a < b

	@staticmethod
	def intLTE(a, b):
		"""
		Checks if a <= b, where :attr:`OMEGA` is larger than every integer.

		Args:
			a:	Either an integer, or :attr:`OMEGA`.
			b:	Either an integer, or :attr:`OMEGA`.
		"""
		return not PetriNet.intLT(b, a)

	def graphviz(self):
		"""
		Obtains the net as a Graphviz file.
		"""
		res = "digraph Net {\n"
		map = {}
		for ip, p in enumerate(self.places.values()):
			res += "\tP%i [label=\"%s\\n%i\"];\n" % (ip, p[0], p[1])
			map[p[0]] = "P%i" % ip
		for it, t in enumerate(self.transitions.values()):
			res += "\tT%i [label=\"%s\", shape=box];\n" % (it, t)
			map[t] = "T%i" % it
		for arc in self.arcs.values():
			source, target, inh, weight = arc
			shape = ""
			if inh:
				shape = ",arrowhead=odot"
			res += "\t%s -> %s [label=\"%i\"%s];\n" % (map[source], map[target], weight, shape)
		res += "}\n"
		return res


	def reachabilityGraph(self, title, start, limit, table=None):
		"""
		Constructs a Reachability Graph for the given net, starting from the
		current marking. This results in a GraphViz string.

		Args:
			title (str):	The title for the graph.
			start (str):	The shape for the start node.
			limit (int):	The maximal amount of markings to expand.
							This prevents infinite loops.
			table (str):	When given, the markings are written to this CSV file
							and the nodes only show their names.
		"""
		initial = self.getMarking()[:]
		markings = { "S0": initial }
		imarks = { tuple(initial): "S0" }
		edges = {}

		stack = ["S0"]
		expanded = 0
		while len(stack) > 0 and expanded < limit:
			S = stack.pop()
			self.setMarking(markings[S])
			for t, n in self.nextMarkings():
				tn = tuple(n)
				if tn not in imarks:
					name = "S%d" % len(markings)
					imarks[tn] = name
					markings[name] = n
					stack.append(name)
				edges.setdefault((S, imarks[tn]), set()).add(t)
			expanded += 1

		self.setMarking(initial)
		if len(stack) > 0:
			log("WARNING: The Reachability Graph's construction was prematurely terminated.\n"
				"         It may be infinite. Try generating the Coverability Graph instead.")
		return self._graph("RG", title, start, markings, edges, table)

	def _graph(self, kind, title, start, markings, edges, table):
		"""
		Converts a constructed graph to GraphViz and optionally writes the
		markings to a CSV table.
		"""
		log("Creating graph with %i nodes..." % len(markings))
		if len(markings) > 1000:
			log("WARNING: There are over 1000 nodes in the graph. It may not be displayable.")

		if table is not None:
			with open(table, "w", encoding="utf-8") as file:
				file.write("state," + ",".join(self.places[p][0] for p in self._mvec) + "\n")
				for k, v in markings.items():
					file.write(k + "," + ",".join(str(x) for x in v) + "\n")

		dot = "digraph %s {\n" % kind
		dot += "  label=\"%s\";\n" % title
		dot += "  labelloc=t;\n"
		for k, v in markings.items():
			attrs = []
			if k == "S0":
				attrs.append("shape=%s" % start)
			if table is None:
				attrs.append("label=\"%s\"" % self.toString(v))
			dot += "  %s%s;\n" % (k, " [%s]" % ", ".join(attrs) if attrs else "")
		for (s, m), t in edges.items():
			dot += "  %s -> %s [label=\"%s\"];\n" % (s, m, ", ".join(str(x) for x in sorted(t)))
		return dot + "}\n"

	def inhibitorPlaces(self):
		"""
		Obtains the marking-vector indices of all places that are the source of an inhibitor arc.
		"""
		return { self._mvec.index(source) for source, _, inh, _ in self.arcs.values() if inh and source in self.places }

	def accelerate(self, n, S, markings, parent, inhibited):
		"""
		Replaces the entries of the new marking :code:`n` by :attr:`OMEGA`
		wherever it strictly covers an ancestor of :code:`n` (Karp-Miller).
		Only the path from the start to :code:`S`, the node that produced
		:code:`n`, is considered: a marking elsewhere in the graph says
		nothing about the firing sequence that led to :code:`n`.

		An ancestor is skipped if it differs from :code:`n` on a place tested
		by an inhibitor arc, because the extra tokens there could disable the
		sequence that would otherwise repeat forever.

		Args:
			n (list):			The new marking; modified in place.
			S (str):			The name of the node that produced :code:`n`.
			markings (dict):	Node name to marking.
			parent (dict):		Node name to the name of its parent in the search tree.
			inhibited (set):	Indices of places tested by inhibitor arcs.
		"""
		changed = True
		while changed:
			changed = False
			node = S
			while node is not None:
				M = markings[node]
				if self.markingDominates(n, M) and all(n[j] == M[j] for j in inhibited):
					for j in range(len(n)):
						if n[j] != OMEGA and self.intLT(M[j], n[j]):
							n[j] = OMEGA
							changed = True
				node = parent[node]

	def coverabilityGraph(self, title, start, limit=0, table=None):
		"""
		Constructs a Coverability Graph for the given net, starting from the
		current marking. This results in a GraphViz string.

		Args:
			title (str):	The title for the graph.
			start (str):	The shape for the start node.
			limit (int):	The maximal amount of markings to expand; 0 means no limit.
							Without inhibitor arcs construction always ends, so this
							only guards against very large graphs.
			table (str):	When given, the markings are written to this CSV file
							and the nodes only show their names.
		"""
		initial = self.getMarking()[:]
		markings = { "S0": initial }
		imarks = { tuple(initial): "S0" }
		parent = { "S0": None }
		edges = {}
		inhibited = self.inhibitorPlaces()

		if inhibited:
			log("WARNING: The net has inhibitor arcs on %s.\n"
				"         Their places are never set to %s, so the graph may not terminate\n"
				"         if one of them is unbounded." % ([self.places[self._mvec[j]][0] for j in sorted(inhibited)], OMEGA))

		stack = ["S0"]
		expanded = 0
		while len(stack) > 0 and (limit == 0 or expanded < limit):
			S = stack.pop()
			self.setMarking(markings[S])
			for t, n in self.nextMarkings():
				self.accelerate(n, S, markings, parent, inhibited)
				tn = tuple(n)
				if tn not in imarks:
					name = "S%d" % len(markings)
					imarks[tn] = name
					markings[name] = n
					parent[name] = S
					stack.append(name)
				edges.setdefault((S, imarks[tn]), set()).add(t)
			expanded += 1

		self.setMarking(initial)
		if len(stack) > 0:
			log("WARNING: The Coverability Graph's construction was prematurely terminated.\n"
				"         The graph may be incomplete.")
		return self._graph("CG", title, start, markings, edges, table)

	def getIncidenceMatrix(self):
		"""
		Obtains the incidence matrix of the net.
		"""
		C = []
		for _ in range(len(self.places)):
			C.append([0] * len(self.transitions))

		torder = sorted(self.transitions.keys())
		for tix in range(len(torder)):
			t = torder[tix]
			arcs = self._sa.get(t, [])
			for ax in arcs:
				a = self.arcs[ax]
				if not a[2] and a[1] in self._mvec:
					C[self._mvec.index(a[1])][tix] += a[-1]
			arcs = self._ta.get(t, [])
			for ax in arcs:
				a = self.arcs[ax]
				if not a[2] and a[0] in self._mvec:
					C[self._mvec.index(a[0])][tix] -= a[-1]
		return C

	def Pinv(self):
		"""
		Compute the P-invariants of the net.
		"""
		invs = Matrix.farkas(self.getIncidenceMatrix())
		if len(invs) == 0:
			return ""
		res = ""
		for places in invs:
			s = 0
			for pi in range(len(places)):
				if places[pi] == 0: continue
				place = self.places[self._mvec[pi]]
				if places[pi] == 1:
					res += "M(%s) + " % place[0]
				else:
					res += "%i * M(%s) + " % (places[pi], place[0])
				s += place[1] * places[pi]
			res = res[:-2] + "= %i\n" % s
		return res[:-1]

	def Tinv(self):
		"""
		Compute the T-invariants of the net.
		This might take a long time, so it is not possible by default.
		"""
		C = self.getIncidenceMatrix()
		C = Matrix.transpose(C)
		invs = Matrix.farkas(C)
		return invs

class Matrix:
	@staticmethod
	def transpose(matrix):
		"""
		Transposes a matrix (list of lists).
		"""
		m = len(matrix)
		if m == 0:
			return []
		n = len(matrix[0])
		new = [[0] * m for _ in range(n)]
		for mi in range(m):
			for ni in range(n):
				new[ni][mi] = matrix[mi][ni]
		return new

	@staticmethod
	def farkas(C):
		"""
		Computes the linear optimization of a matrix.
		Based on:
			http://www.lsv.fr/~schwoon/enseignement/verification/ws0910/nets2
		"""
		n = len(C)
		if n == 0:
			return []
		m = len(C[0])
		En = [[1 if x == y else 0 for x in range(n)] for y in range(n)]
		D = []
		for i in range(n):
			D.append(C[i] + En[i])
		for i in range(m):
			ta = []
			for d1 in D:
				for d2 in D:
					if d1[i] * d2[i] < 0:
						d = [abs(d2[i]) * d1[u] + abs(d1[i]) * d2[u] for u in range(m+n)]
						assert d[i] == 0
						dp = [x // gcd(d) for x in d]
						if dp not in D:
							D.append(dp)
							break
			for j in range(len(D)-1, -1, -1):
				if D[j][i] != 0:
					D.pop(j)
		for j in range(len(D)):
			for _ in range(m):
				D[j].pop(0)
		return list(set([tuple(d) for d in D]))



COMMANDS = ("reachability", "coverability", "invariants", "net")


def expand_command(argv):
	"""
	Replaces an unambiguous prefix of a command (e.g. "c") by the full command name.
	"""
	if len(argv) > 0 and not argv[0].startswith("-"):
		matches = [c for c in COMMANDS if c.startswith(argv[0].lower())]
		if len(matches) == 1:
			return [matches[0]] + argv[1:]
	return argv


def main(argv=None):
	import argparse

	def non_negative(value):
		val = int(value)
		if val < 0:
			raise argparse.ArgumentTypeError("The limit cannot be negative.")
		return val

	parser = argparse.ArgumentParser(description="Analyse a TAPAAL P/T net: build its Reachability or Coverability Graph, "
									"find its P-Invariants, or export the net itself.")
	commands = parser.add_subparsers(dest="command", required=True, metavar="command")

	def graph_command(name, help, limit_help, default_limit):
		sub = commands.add_parser(name, help=help)
		sub.add_argument('input', help="The *.tapn file.")
		sub.add_argument('-o', '--output', help="Write the GraphViz graph to this file instead of the console.")
		sub.add_argument('--table', metavar="CSV", help="Write the markings to this CSV file and only show node names in the graph.")
		sub.add_argument('--limit', type=non_negative, default=default_limit, help=limit_help)
		sub.add_argument('-t', '--title', help="The title of the graph. Defaults to the kind of graph.")
		sub.add_argument('-s', '--start', default="box", help="The GraphViz shape of the start node. Defaults to 'box'.")
		return sub

	graph_command("reachability", "Build the Reachability Graph.",
				"The maximal amount of markings to expand. Defaults to 1000.", 1000)
	graph_command("coverability", "Build the Coverability Graph.",
				"The maximal amount of markings to expand. Defaults to 0, meaning no limit.", 0)

	sub = commands.add_parser("invariants", help="Print the P-Invariants of the net.")
	sub.add_argument('input', help="The *.tapn file.")

	sub = commands.add_parser("net", help="Export the net as the script reads it, to check it against TAPAAL.")
	sub.add_argument('input', help="The *.tapn file.")
	sub.add_argument('-o', '--output', help="Write the GraphViz net to this file instead of the console.")

	args = parser.parse_args(expand_command(sys.argv[1:] if argv is None else argv))
	net = PetriNet(args.input)

	if args.command == "invariants":
		invs = net.Pinv()
		print(invs if invs != "" else "The net has no P-Invariants.")
		return

	if args.command == "net":
		result = net.graphviz()
	else:
		log("The markings are given w.r.t. the following places: %s" % [net.places[x][0] for x in net._mvec])
		title = args.title or args.command.capitalize() + " Graph"
		if args.command == "reachability":
			result = net.reachabilityGraph(title, args.start, args.limit, args.table)
		else:
			result = net.coverabilityGraph(title, args.start, args.limit, args.table)

	if args.output is None:
		sys.stdout.write(result)
	else:
		with open(args.output, "w", encoding="utf-8") as file:
			file.write(result)


if __name__ == '__main__':
	main()
