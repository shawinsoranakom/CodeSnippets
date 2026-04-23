def _write_ftstring_inner(self, node, is_format_spec=False):
        if isinstance(node, JoinedStr):
            # for both the f-string itself, and format_spec
            for value in node.values:
                self._write_ftstring_inner(value, is_format_spec=is_format_spec)
        elif isinstance(node, Constant) and isinstance(node.value, str):
            value = node.value.replace("{", "{{").replace("}", "}}")

            if is_format_spec:
                value = value.replace("\\", "\\\\")
                value = value.replace("'", "\\'")
                value = value.replace('"', '\\"')
                value = value.replace("\n", "\\n")
            self.write(value)
        elif isinstance(node, FormattedValue):
            self.visit_FormattedValue(node)
        elif isinstance(node, Interpolation):
            self.visit_Interpolation(node)
        else:
            raise ValueError(f"Unexpected node inside JoinedStr, {node!r}")