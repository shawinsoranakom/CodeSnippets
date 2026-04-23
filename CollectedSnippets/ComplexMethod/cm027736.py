def visit_functiondef(self, node: nodes.FunctionDef) -> None:
        """Apply relevant type hint checks on a FunctionDef node."""
        annotations = _get_all_annotations(node)

        # Check method or function matchers.
        if node.is_method():
            matchers = _METHOD_MATCH
        else:
            if self._in_test_module and node.parent is self._module_node:
                if node.name.startswith("test_"):
                    self._check_test_function(node, False)
                    return
                if (decoratornames := node.decoratornames()) and (
                    # `@pytest.fixture`
                    "_pytest.fixtures.fixture" in decoratornames
                    # `@pytest.fixture(...)`
                    or "_pytest.fixtures.FixtureFunctionMarker" in decoratornames
                ):
                    self._check_test_function(node, True)
                    return
            matchers = self._function_matchers

        # Check that common arguments are correctly typed.
        if not self.linter.config.ignore_missing_annotations:
            for arg_name, expected_type in _COMMON_ARGUMENTS.items():
                arg_node, annotation = _get_named_annotation(node, arg_name)
                if arg_node and not _is_valid_type(expected_type, annotation):
                    self.add_message(
                        "hass-argument-type",
                        node=arg_node,
                        args=(arg_name, expected_type, node.name),
                    )

        for match in matchers:
            if not match.need_to_check_function(node):
                continue
            self._check_function(node, match, annotations)