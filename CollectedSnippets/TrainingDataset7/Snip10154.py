def add_node(self, key, migration):
        assert key not in self.node_map
        node = Node(key)
        self.node_map[key] = node
        self.nodes[key] = migration