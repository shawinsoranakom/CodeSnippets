def visit_classdef(self, node: nodes.ClassDef) -> None:
        """Apply relevant type hint checks on a ClassDef node."""
        if self._module_platform not in {"number", "sensor"}:
            return

        ancestors = [a.name for a in node.ancestors()]
        if (
            "RestoreEntity" in ancestors
            and "SensorEntity" in ancestors
            and "RestoreSensor" not in ancestors
        ):
            self.add_message(
                "hass-invalid-inheritance",
                node=node,
                args="SensorEntity and RestoreEntity should not be combined, please use RestoreSensor",
            )
        elif (
            "RestoreEntity" in ancestors
            and "NumberEntity" in ancestors
            and "RestoreNumber" not in ancestors
        ):
            self.add_message(
                "hass-invalid-inheritance",
                node=node,
                args="NumberEntity and RestoreEntity should not be combined, please use RestoreNumber",
            )