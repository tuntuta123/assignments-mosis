"""
CBD simulator skeleton.
"""

from .linear_solver import is_linear, solve_linear_loop
from .model import CBD, Signal


__all__ = [
    "DependencyGraph",
    "strongly_connected_components",
    "topological_sort",
    "is_algebraic_loop",
    "Simulator",
]


class DependencyGraph:
    """Directed graph of "depends on" relations between blocks.

    ``addDependency(dependent, influencer)`` records that ``dependent`` reads
    a value produced by ``influencer``, so ``influencer`` must be computed
    first. A block may depend on itself.
    """

    def __init__(self):
        self._order = []
        self._influencers = {}
        self._dependents = {}

    def addNode(self, block):
        if block in self._influencers:
            return
        self._order.append(block)
        self._influencers[block] = []
        self._dependents[block] = []

    def addDependency(self, dependent, influencer):
        self.addNode(dependent)
        self.addNode(influencer)
        if influencer not in self._influencers[dependent]:
            self._influencers[dependent].append(influencer)
            self._dependents[influencer].append(dependent)

    def getInfluencers(self, block):
        """Blocks that ``block`` depends on."""
        return list(self._influencers.get(block, []))

    def getDependents(self, block):
        """Blocks that depend on ``block``."""
        return list(self._dependents.get(block, []))

    def nodes(self):
        return list(self._order)


def strongly_connected_components(dep_graph):
    """Group the blocks into strongly connected components.

    The result is a list of components, and each component is a list of
    blocks. A component of one block that does not depend on itself is an
    ordinary block. Every other component is an algebraic loop. This list
    is not a computation order. ``topological_sort`` produces that order.
    """
    index = 0
    stack = []
    on_stack = set()
    indices = {}
    lowlink = {}
    components = []

    def strongconnect(block):
        nonlocal index
        indices[block] = index
        lowlink[block] = index
        index += 1
        stack.append(block)
        on_stack.add(block)
        for influencer in dep_graph.getInfluencers(block):
            if influencer not in indices:
                strongconnect(influencer)
                lowlink[block] = min(lowlink[block], lowlink[influencer])
            elif influencer in on_stack:
                lowlink[block] = min(lowlink[block], indices[influencer])
        if lowlink[block] == indices[block]:
            component = []
            while True:
                member = stack.pop()
                on_stack.remove(member)
                component.append(member)
                if member is block:
                    break
            components.append(component)

    for block in dep_graph.nodes():
        if block not in indices:
            strongconnect(block)

    covered = [block for component in components for block in component]
    if len(covered) != len(set(covered)) or set(covered) != set(dep_graph.nodes()):
        raise RuntimeError("Component search did not cover every block exactly once.")
    return components


def topological_sort(dep_graph, components):
    """Order components so each block is computed after the blocks it reads.

    A component that reads a block in another component comes later. The
    sort is over components, not over the blocks inside a loop: those have
    no valid order and are solved together. A cycle in this graph means two
    components should have been one.
    """
    owner = {}
    for index, component in enumerate(components):
        for block in component:
            owner[block] = index

    incoming = [set() for _ in components]
    outgoing = [[] for _ in components]
    for index, component in enumerate(components):
        for block in component:
            for influencer in dep_graph.getInfluencers(block):
                other = owner[influencer]
                if other != index and other not in incoming[index]:
                    incoming[index].add(other)
                    outgoing[other].append(index)

    remaining = [len(preds) for preds in incoming]
    ready = [index for index, count in enumerate(remaining) if count == 0]
    ordered = []
    while ready:
        index = ready.pop(0)
        ordered.append(components[index])
        for dependent in outgoing[index]:
            remaining[dependent] -= 1
            if remaining[dependent] == 0:
                ready.append(dependent)
    if len(ordered) != len(components):
        raise RuntimeError("Component graph has a cycle.")
    return ordered


def is_algebraic_loop(component, dep_graph):
    """True when the blocks in ``component`` must be solved together.

    A component of more than one block is a loop. A single block is a loop
    only when it depends on itself.
    """
    if len(component) > 1:
        return True
    if len(component) == 1:
        block = component[0]
        return block in dep_graph.getInfluencers(block)
    return False


class Simulator:
    """Computes a CBD model at a fixed time step.

    The dependency graph is built for iteration 0 and again for iteration 1,
    because a delay block changes its dependencies between those two
    iterations. Later iterations reuse the second graph.
    """

    def __init__(self, model):
        self.model = model
        self._delta_t = 1.0
        self._dep_graph = None

    def setDeltaT(self, delta_t):
        if delta_t <= 0:
            raise ValueError("delta_t must be positive.")
        self._delta_t = delta_t

    def getDeltaT(self):
        return self._delta_t

    def run(self, term_time):
        """Simulate from time 0 up to ``term_time``.

        An iteration at time ``t`` is computed while ``|term_time - t|`` is
        at least one step. With ``delta_t`` 0.1 and ``term_time`` 1 the
        computed times are 0, 0.1, ..., 0.9.
        """
        if term_time is None:
            raise ValueError("term_time is required.")
        if self._delta_t <= 0:
            raise ValueError("delta_t must be positive.")
        iteration = 0
        time = 0.0
        while round(abs(term_time - time), 8) >= self._delta_t:
            self._step(iteration, time)
            iteration += 1
            time += self._delta_t

    def _collect_atomic_blocks(self, cbd):
        """Return the atomic blocks in ``cbd``, descending into nested CBDs.
        The dependency graph is built over this list.
        """
        atomic_blocks = []

        for block in cbd.getBlocks():
            if isinstance(block, CBD): #found CBD, then iterate the inner blocks
                atomic_blocks.extend(self._collect_atomic_blocks(block))
            else:
                atomic_blocks.append(block)

        return atomic_blocks

    def _build_dependency_graph(self, curIteration):
        """Build the dependency graph of the atomic blocks at ``curIteration``.

        Add every atomic block as a node. 
        For each block, ask ``getDependencies`` and record those blocks as influencers. 
        The edge means "this block reads a value produced by that block".
        """
        graph = DependencyGraph()
        blocks = self._collect_atomic_blocks(self.model)

        for block in blocks:
            graph.addNode(block)

        for block in blocks:
            dependencies = block.getDependencies(curIteration)

            for dependency in dependencies:
                graph.addDependency(block, dependency)

        return graph
        
    def _step(self, curIteration, time):
        """Compute every atomic block once, then update the CBD output ports.

        Rebuild ``self._dep_graph`` at every iteration. Find the components with
        ``strongly_connected_components``, order them with ``topological_sort``,
        and walk that list:

        - a normal component has one block: call its ``compute``
        - an algebraic loop that ``is_linear`` accepts: call ``solve_linear_loop``
        - any other loop raises ``ValueError``

        Finish by copying atomic outputs onto the CBD ports that expose them.
        """
        # TODO: Part 1, Task 4
        raise NotImplementedError("Simulator._step")

    def _update_cbd_ports(self, cbd, time):
        """Copy each nested output onto the CBD port that exposes it.

        Atomic blocks already store their own outputs. Reading
        ``model.getSignalHistory("OUT1")`` on a CBD needs that value on the
        boundary port as well. Descend into nested CBDs, then update this
        level. ``Port.getSourcePort`` finds the atomic output behind a
        boundary port.
        """
        # TODO: Part 1, Task 4
        raise NotImplementedError("Simulator._update_cbd_ports")