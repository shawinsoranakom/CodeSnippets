def _topological_order(self):
        # compute reachable linear nodes, and the set of incoming edges for each node
        order = []
        stack = [self.root]
        seen = set()
        while stack:
            # depth first traversal
            node = stack.pop()
            if node.id in seen:
                continue
            seen.add(node.id)
            order.append(node)
            for label, child in node.linear_edges:
                stack.append(child)

        # do a (slightly bad) topological sort
        incoming = defaultdict(set)
        for node in order:
            for label, child in node.linear_edges:
                incoming[child].add((label, node))
        no_incoming = [order[0]]
        topoorder = []
        positions = {}
        while no_incoming:
            node = no_incoming.pop()
            topoorder.append(node)
            positions[node] = len(topoorder)
            # use "reversed" to make sure that the linear_edges get reorderd
            # from their alphabetical order as little as necessary (no_incoming
            # is LIFO)
            for label, child in reversed(node.linear_edges):
                incoming[child].discard((label, node))
                if not incoming[child]:
                    no_incoming.append(child)
                    del incoming[child]
        # check result
        assert set(topoorder) == set(order)
        assert len(set(topoorder)) == len(topoorder)

        for node in order:
            node.linear_edges.sort(key=lambda element: positions[element[1]])

        for node in order:
            for label, child in node.linear_edges:
                assert positions[child] > positions[node]
        # number the nodes. afterwards every input string in the set has a
        # unique number in the 0 <= number < len(data). We then put the data in
        # self.data into a linear list using these numbers as indexes.
        topoorder[0].num_reachable_linear
        linear_data = [None] * len(self.data)
        inverse = {} # maps value back to index
        for word, value in self.data.items():
            index = self._lookup(word)
            linear_data[index] = value
            inverse[value] = index

        return topoorder, linear_data, inverse