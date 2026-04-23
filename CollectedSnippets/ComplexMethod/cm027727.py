def _check_for_constant_alias(
        self,
        node: nodes.ImportFrom,
        current_component: str | None,
        imported_component: str,
    ) -> bool:
        """Check for hass-import-constant-alias."""
        if current_component == imported_component:
            # Check for `from homeassistant.components.self import DOMAIN as XYZ`
            for name, alias in node.names:
                if name == "DOMAIN" and (alias is not None and alias != "DOMAIN"):
                    self.add_message(
                        "hass-import-constant-unnecessary-alias",
                        node=node,
                        args=(alias, "DOMAIN"),
                    )
                    return False
            return True

        # Check for `from homeassistant.components.other import DOMAIN`
        for name, alias in node.names:
            if name == "DOMAIN" and (alias is None or not alias.endswith("_DOMAIN")):
                self.add_message(
                    "hass-import-constant-alias",
                    node=node,
                    args=(
                        "DOMAIN",
                        "DOMAIN",
                        f"{imported_component.upper()}_DOMAIN",
                    ),
                )
                return False

        return True