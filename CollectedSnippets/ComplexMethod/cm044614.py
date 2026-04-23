def expand(self, indent_size: int) -> Iterable["_Line"]:
        """Expand this line by adding children on their own line."""
        node = self.node
        assert node is not None
        whitespace = self.whitespace
        assert node.children
        if node.key_repr:
            new_line = yield _Line(
                text=f"{node.key_repr}{node.key_separator}{node.open_brace}",
                whitespace=whitespace,
            )
        else:
            new_line = yield _Line(text=node.open_brace, whitespace=whitespace)
        child_whitespace = self.whitespace + " " * indent_size
        tuple_of_one = node.is_tuple and len(node.children) == 1
        for last, child in loop_last(node.children):
            separator = "," if tuple_of_one else node.separator
            line = _Line(
                parent=new_line,
                node=child,
                whitespace=child_whitespace,
                suffix=separator,
                last=last and not tuple_of_one,
            )
            yield line

        yield _Line(
            text=node.close_brace,
            whitespace=whitespace,
            suffix=self.suffix,
            last=self.last,
        )