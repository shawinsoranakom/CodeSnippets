def print_tree(self, height: int = 0) -> None:
    if self.prefix != "":
        print("-" * height, self.prefix, "  (leaf)" if self.is_leaf else "")

    for value in self.nodes.values():
        value.print_tree(height + 1)
