def _get_view_inverse_node_usages(
    later_node_usages: set[Node], self_aliases: set[Node]
) -> set[Node]:
    def matching_view_metadata(a: FakeTensor, b: FakeTensor) -> bool:
        return (
            a.size() == b.size()
            and a.stride() == b.stride()
            and a.storage_offset() == b.storage_offset()
        )

    view_inverse_nodes = set()
    # Go through them in node order, so we can see chains of view_scatter ops.
    for n in sorted(later_node_usages, key=lambda x: x.meta["node_idx"]):
        if n.target not in _VIEW_INVERSE_MAP:
            continue
        base = n.args[0]
        mutated_view = n.args[1]
        if not isinstance(base, Node):
            raise AssertionError(f"Expected Node for base, got {type(base)}")
        if not isinstance(base.meta["fake_result"], FakeTensor):
            raise AssertionError("Expected FakeTensor in base.meta['fake_result']")
        if not isinstance(mutated_view, Node):
            raise AssertionError(
                f"Expected Node for mutated_view, got {type(mutated_view)}"
            )
        if not isinstance(mutated_view.meta["fake_result"], FakeTensor):
            raise AssertionError(
                "Expected FakeTensor in mutated_view.meta['fake_result']"
            )
        if isinstance(n.target, str):
            raise AssertionError("n.target should not be a string")
        # Check that this view_inverse op actually corresponds to taking doing the inverse
        # of one of our existing self_alias nodes.
        original_view = _VIEW_INVERSE_MAP[n.target]
        for self_alias in self_aliases:
            # We're looking for some alias of the self arg, "alias",
            # that was created from some op `alias = foo(base, args...)`
            # such that the current _scatter op "inverts" that foo call.
            # We can check that by running the original op again, and checking that the strides match.
            if "view_of" not in self_alias.meta:
                continue
            self_alias_base = self_alias.meta["view_of"]
            try:
                # The we're trying to reuse the args from the view_scatter call inside of the corresponding
                # view op, which might throw. This just indicates that view_scatter op isn't a valid inverse
                # of the current alias we're looking at.
                view_replay_metadata = original_view(
                    self_alias_base.meta["fake_result"], *n.args[2:], **n.kwargs
                )
                expected_metadata = self_alias.meta["fake_result"]
                # If the alias and its base both have matching metadata, then this view_scatter op is valid to re-inplace.
                if matching_view_metadata(
                    self_alias_base.meta["fake_result"], base.meta["fake_result"]
                ) and matching_view_metadata(view_replay_metadata, expected_metadata):
                    view_inverse_nodes.add(n)
            except Exception:
                continue

    return view_inverse_nodes