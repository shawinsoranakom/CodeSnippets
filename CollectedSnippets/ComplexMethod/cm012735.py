def find_layout_arg(
        self, node: IRNode, attr: ValidLayoutAttrs, dim: int
    ) -> LayoutArg | None:
        matches = [
            arg
            for arg in itertools.chain.from_iterable(self.layout_args.values())
            if arg.matches(node, attr, dim)
        ]
        if len(matches) >= 1:
            # Verify all matches have the same node, attribute, and dimension
            # And if they come from the same node, whichever symbol we use is fine.
            # if in runtime the logic changes, this would trigger guard
            first_match = matches[0]
            if not all(
                match.node == first_match.node
                and match.attr == first_match.attr
                and match.dim == first_match.dim
                for match in matches
            ):
                raise AssertionError("All matching layout args should be identical")
            return first_match
        attr_values = node.get_size() if attr == "size" else node.get_stride()
        if dim >= len(attr_values):
            return None
        expr = attr_values[dim]
        fallback_matches = []
        for arg in itertools.chain.from_iterable(self.layout_args.values()):
            if arg.attr != attr:
                continue
            if arg.node.get_name() != node.get_name():
                continue
            arg_values = (
                arg.node.get_size() if arg.attr == "size" else arg.node.get_stride()
            )
            if arg.dim >= len(arg_values):
                continue
            if arg_values[arg.dim] == expr:
                fallback_matches.append(arg)
        if fallback_matches:
            return fallback_matches[0]
        return None