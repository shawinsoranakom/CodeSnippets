def should_ban_recomputation(node: fx.Node) -> str | None:
        """Returns reason string if node should be banned from recomputation, None otherwise."""
        if node.op != "call_function":
            return None
        if node.target is operator.getitem:
            return None
        if node.meta.get("recompute", None) == CheckpointPolicy.MUST_SAVE:
            return "marked MUST_SAVE"
        if config.recompute_views and op_types.is_view(node):
            return None
        if node.target in [aten.lift_fresh_copy.default, aten.lift_fresh.default]:
            return None

        if min_cut_options.ban_if_not_in_allowlist:
            if not op_types.is_recomputable(node):
                return "not in recomputable allowlist"
        else:
            if op_types.is_random(node):
                return "random op"
            if op_types.is_compute_intensive(node):
                return "compute intensive op"
            if is_non_builtin_to_include(node):
                return "non-builtin op"

        # If a node *must* be materialized in the backwards pass, then we
        # should never recompute it. This is a pretty subtle point.  In
        # general, the assumption we make is that recomputing a node in the
        # backwards pass is "free". However, if a node must be materialized
        # in the backwards pass, then recomputing it is never free.
        if min_cut_options.ban_if_materialized_backward and is_materialized_backwards(
            node
        ):
            log.debug("materialized backwards: %s %s", node, tuple(node.users))
            return "materialized in backward"

        # Arbitrary hack that sometimes seems to help things. The above
        # modification appears to have made this heuristic a lot less critical
        # for performance.
        # NB: As of PR #121692, this hack no longer seems necessary.
        if (
            # pyrefly: ignore [missing-attribute]
            node.dist_from_bw < 1000 and node.dist_from_bw > config.max_dist_from_bw
        ):
            return "too far from backward"

        # If the output of an op is 4x smaller (arbitrary choice),
        # then we don't allow recomputation. The idea here is that for
        # things like reductions, saving the output of the reduction is very
        # cheap/small, and it makes sure we don't do things like recompute
        # normalizations in the backwards.
        if min_cut_options.ban_if_reduction:
            input_tensors_size = sum(
                _size_of(i) for i in node.args if isinstance(i, fx.Node)
            )
            output_size = _size_of(node)
            if output_size * 4 < input_tensors_size:
                return "reduction op"
        return None