def _linearize_edges(self):
        # compute "linear" edges. the idea is that long chains of edges without
        # any of the intermediate states being final or any extra incoming or
        # outgoing edges can be represented by having removing them, and
        # instead using longer strings as edge labels (instead of single
        # characters)
        incoming = defaultdict(list)
        nodes = sorted(self.enum_all_nodes(), key=lambda e: e.id)
        for node in nodes:
            for label, child in sorted(node.edges.items()):
                incoming[child].append(node)
        for node in nodes:
            node.linear_edges = []
            for label, child in sorted(node.edges.items()):
                s = [label]
                while len(child.edges) == 1 and len(incoming[child]) == 1 and not child.final:
                    (c, child), = child.edges.items()
                    s.append(c)
                node.linear_edges.append((''.join(s), child))