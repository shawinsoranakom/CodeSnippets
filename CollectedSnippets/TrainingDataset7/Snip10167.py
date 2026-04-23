def __repr__(self):
        nodes, edges = self._nodes_and_edges()
        return "<%s: nodes=%s, edges=%s>" % (self.__class__.__name__, nodes, edges)