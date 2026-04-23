def ensure_not_cyclic(self):
        # Algo from GvR:
        # https://neopythonic.blogspot.com/2009/01/detecting-cycles-in-directed-graph.html
        todo = set(self.nodes)
        while todo:
            node = todo.pop()
            stack = [node]
            while stack:
                top = stack[-1]
                for child in self.node_map[top].children:
                    # Use child.key instead of child to speed up the frequent
                    # hashing.
                    node = child.key
                    if node in stack:
                        cycle = stack[stack.index(node) :]
                        raise CircularDependencyError(
                            ", ".join("%s.%s" % n for n in cycle)
                        )
                    if node in todo:
                        stack.append(node)
                        todo.remove(node)
                        break
                else:
                    node = stack.pop()