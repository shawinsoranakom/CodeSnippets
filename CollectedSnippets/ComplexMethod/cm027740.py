def _do_micro_check(
        self, target: nodes.NodeNG, node: nodes.Assign | nodes.AnnAssign
    ) -> None:
        """Check const assignment is not containing ANSI micro char."""

        def _check_const(node_const: nodes.Const | Any) -> bool:
            if (
                isinstance(node_const, nodes.Const)
                and isinstance(node_const.value, str)
                and "\u00b5" in node_const.value
            ):
                self.add_message(self.name, node=node)
                return True
            return False

        # Check constant assignments
        if (
            isinstance(target, nodes.AssignName)
            and isinstance(node.value, nodes.Const)
            and _check_const(node.value)
        ):
            return

        # Check dict with EntityDescription calls
        if isinstance(target, nodes.AssignName) and isinstance(node.value, nodes.Dict):
            for _, subnode in node.value.items:
                if not isinstance(subnode, nodes.Call):
                    continue
                for keyword in subnode.keywords:
                    if _check_const(keyword.value):
                        return