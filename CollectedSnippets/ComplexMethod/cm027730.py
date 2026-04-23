def _check_pytest_fixture(
        self, node: nodes.FunctionDef, decoratornames: set[str]
    ) -> None:
        if (
            "_pytest.fixtures.FixtureFunctionMarker" not in decoratornames
            or not (root_name := node.root().name).startswith("tests.")
            or (decorator := self._get_pytest_fixture_node(node)) is None
            or not (
                scope_keyword := self._get_pytest_fixture_node_keyword(
                    decorator, "scope"
                )
            )
            or not isinstance(scope_keyword.value, nodes.Const)
            or not (scope := scope_keyword.value.value)
        ):
            return

        parts = root_name.split(".")
        test_component: str | None = None
        if root_name.startswith("tests.components.") and parts[2] != "conftest":
            test_component = parts[2]

        if scope == "session":
            if test_component:
                self.add_message(
                    "hass-pytest-fixture-decorator",
                    node=decorator,
                    args=("scope `session`", "use `package` or lower"),
                )
                return
            if not (
                autouse_keyword := self._get_pytest_fixture_node_keyword(
                    decorator, "autouse"
                )
            ) or (
                isinstance(autouse_keyword.value, nodes.Const)
                and not autouse_keyword.value.value
            ):
                self.add_message(
                    "hass-pytest-fixture-decorator",
                    node=decorator,
                    args=(
                        "scope/autouse combination",
                        "set `autouse=True` or reduce scope",
                    ),
                )
            return

        test_module = parts[3] if len(parts) > 3 else ""

        if test_component and scope == "package" and test_module != "conftest":
            self.add_message(
                "hass-pytest-fixture-decorator",
                node=decorator,
                args=("scope `package`", "use `module` or lower"),
            )