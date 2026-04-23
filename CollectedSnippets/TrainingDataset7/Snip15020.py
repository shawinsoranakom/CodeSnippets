def visit_node(self, node):
        self.current_path.append(node.name)
        self.node_line_numbers[".".join(self.current_path)] = node.lineno
        self.generic_visit(node)
        self.current_path.pop()