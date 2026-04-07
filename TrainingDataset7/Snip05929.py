def add_edge(self, source, target):
        self.edges.setdefault(source, []).append(target)