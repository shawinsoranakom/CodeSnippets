def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit ImportFrom node."""
        if node.module is None:
            return

        # Exception: we will allow importing the sign path code.
        if (
            node.module == "homeassistant.components.http.auth"
            and len(node.names) == 1
            and node.names[0].name == "async_sign_path"
        ):
            return

        if node.module.startswith("homeassistant.components."):
            # from homeassistant.components.alexa.smart_home import EVENT_ALEXA_SMART_HOME
            # from homeassistant.components.logbook import bla
            self._add_reference(node.module.split(".")[2])

        elif node.module == "homeassistant.components":
            # from homeassistant.components import sun
            for name_node in node.names:
                self._add_reference(name_node.name)