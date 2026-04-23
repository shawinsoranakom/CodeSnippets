def _check_function(
        self,
        node: nodes.FunctionDef,
        match: TypeHintMatch,
        annotations: list[nodes.NodeNG | None],
    ) -> None:
        if self._ignore_function_match(node, annotations, match):
            return
        # Check that all positional arguments are correctly annotated.
        if match.arg_types:
            for key, expected_type in match.arg_types.items():
                if key > len(node.args.args) - 1:
                    # The number of arguments is less than expected
                    self.add_message(
                        "hass-argument-type",
                        node=node,
                        args=(key + 1, expected_type, node.name),
                    )
                    continue
                if node.args.args[key].name in _COMMON_ARGUMENTS:
                    # It has already been checked, avoid double-message
                    continue
                if not _is_valid_type(expected_type, annotations[key]):
                    self.add_message(
                        "hass-argument-type",
                        node=node.args.args[key],
                        args=(key + 1, expected_type, node.name),
                    )

        # Check that all keyword arguments are correctly annotated.
        if match.named_arg_types is not None:
            for arg_name, expected_type in match.named_arg_types.items():
                if arg_name in _COMMON_ARGUMENTS:
                    # It has already been checked, avoid double-message
                    continue
                arg_node, annotation = _get_named_annotation(node, arg_name)
                if arg_node and not _is_valid_type(expected_type, annotation):
                    self.add_message(
                        "hass-argument-type",
                        node=arg_node,
                        args=(arg_name, expected_type, node.name),
                    )

        # Check that kwargs is correctly annotated.
        if match.kwargs_type and not _is_valid_type(
            match.kwargs_type, node.args.kwargannotation
        ):
            self.add_message(
                "hass-argument-type",
                node=node,
                args=(node.args.kwarg, match.kwargs_type, node.name),
            )

        # Check the return type.
        if not _is_valid_return_type(match, node.returns):
            self.add_message(
                "hass-return-type",
                node=node,
                args=(match.return_type or "None", node.name),
            )