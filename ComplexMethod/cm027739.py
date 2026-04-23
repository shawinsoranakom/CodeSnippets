def visit_call(self, node: nodes.Call) -> None:
        """Check for improper log messages."""
        if not isinstance(node.func, nodes.Attribute) or not isinstance(
            node.func.expr, nodes.Name
        ):
            return

        if node.func.expr.name not in LOGGER_NAMES:
            return

        if not node.args:
            return

        first_arg = node.args[0]

        if not isinstance(first_arg, nodes.Const) or not first_arg.value:
            return

        log_message = first_arg.value

        if len(log_message) < 1:
            return

        if log_message[-1] == ".":
            self.add_message("hass-logger-period", node=node)

        if (
            isinstance(node.func.attrname, str)
            and node.func.attrname not in LOG_LEVEL_ALLOWED_LOWER_START
            and log_message[0].upper() != log_message[0]
        ):
            self.add_message("hass-logger-capital", node=node)