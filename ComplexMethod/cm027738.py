def _check_test_function(self, node: nodes.FunctionDef, is_fixture: bool) -> None:
        # Check the return type, should always be `None` for test_*** functions.
        if not is_fixture and not _is_valid_type(None, node.returns, True):
            self.add_message(
                "hass-return-type",
                node=node,
                args=("None", node.name),
            )
        # Check that all positional arguments are correctly annotated.
        for arg_name, expected_type in _TEST_FIXTURES.items():
            arg_node, annotation = _get_named_annotation(node, arg_name)
            if arg_node and expected_type == "None" and not is_fixture:
                self.add_message(
                    "hass-consider-usefixtures-decorator",
                    node=arg_node,
                    args=(arg_name, expected_type, node.name),
                )
            if arg_node and not _is_valid_type(expected_type, annotation):
                self.add_message(
                    "hass-argument-type",
                    node=arg_node,
                    args=(arg_name, expected_type, node.name),
                )