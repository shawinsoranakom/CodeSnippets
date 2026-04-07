def get_nodes_by_type(self, nodetype):
        """
        Return a list of all nodes (within this node and its nodelist)
        of the given type
        """
        nodes = []
        if isinstance(self, nodetype):
            nodes.append(self)
        for attr in self.child_nodelists:
            nodelist = getattr(self, attr, None)
            if nodelist:
                nodes.extend(nodelist.get_nodes_by_type(nodetype))
        return nodes