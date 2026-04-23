def _match_nodes(
        self, pn: Node, gn: Node, match: InternalMatch, node_name_match: str = ""
    ) -> bool:
        logger.info("  matching %s to %s", pn, gn)

        if not (isinstance(pn, Node) and isinstance(gn, Node)):
            raise AssertionError(f"pn and gn must be Node, pn: {pn}, gn: {gn}")

        # Check if we've already matched these nodes in the current
        # traversal
        if pn in match.nodes_map:
            return match.nodes_map[pn] == gn

        # TODO: use a more efficient way to check if gn is matched before: two-way dict
        if gn in match.nodes_map.values():
            return False

        if not self._nodes_are_equal(pn, gn, node_name_match):
            return False

        # Optimistically mark `pn` as a match for `gn`, and save a local copy of match
        saved_match = copy.copy(match)
        match.nodes_map[pn] = gn

        # Placeholder is a wildcard and can be matched with any python object
        # (including list/tuple)
        if pn.op == "placeholder":
            return True

        # Recursively traverse upwards to check if `pn` is a true
        # match for `gn`
        match_found = True

        def _match_args(
            args1: list[Any] | tuple[Any, ...], args2: list[Any] | tuple[Any, ...]
        ) -> bool:
            if len(args1) != len(args2):
                return False

            for a1, a2 in zip(args1, args2):
                if isinstance(a1, Node) and isinstance(a2, Node):
                    matched = self._match_nodes(a1, a2, match)
                elif isinstance(a1, (list, tuple)) and isinstance(a2, (list, tuple)):
                    matched = _match_args(a1, a2)
                else:
                    matched = (
                        self._match_literals(a1, a2, match) or self.ignore_literals
                    )

                if not matched:
                    return False

            return True

        # Flatten all args/kwargs into 1 list of args
        pn_args: list[Any] | None = None
        gn_args: list[Any] | None = None
        if (
            (
                len(pn.args) != len(gn.args)
                or list(pn.kwargs.keys()) != list(gn.kwargs.keys())
            )
            and pn.op == "call_function"
            and isinstance(pn.target, torch._ops.OpOverload)
        ):
            args_schema = pn.target._schema.arguments

            def get_all_arguments(
                orig_args: tuple[Any, ...], orig_kwargs: dict[str, Any]
            ) -> list[Any]:
                all_args = []
                for i, schema in enumerate(args_schema):
                    if schema.name in orig_kwargs:
                        all_args.append(orig_kwargs[schema.name])
                    elif not schema.kwarg_only and i < len(orig_args):
                        all_args.append(orig_args[i])
                    else:
                        all_args.append(schema.default_value)
                return all_args

            pn_args = get_all_arguments(pn.args, pn.kwargs)
            gn_args = get_all_arguments(gn.args, gn.kwargs)

        elif len(pn.args) == len(gn.args) and list(pn.kwargs.keys()) == list(
            gn.kwargs.keys()
        ):
            pn_args = list(pn.args)
            gn_args = list(gn.args)
            pn_args.extend(list(pn.kwargs.values()))
            gn_args.extend(list(gn.kwargs.values()))
        else:
            match_found = False

        match_found = (
            match_found
            and pn_args is not None
            and gn_args is not None
            and _match_args(pn_args, gn_args)
        )

        if not match_found:
            # revert to saved_match before matching with current node
            match = copy.copy(saved_match)
            return False

        return True