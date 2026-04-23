def visit_subscript(self, node: nodes.Subscript) -> None:
        """Check for hass.data[DOMAIN] access."""
        if not _is_hass_data_domain_access(node):
            return

        root_name = node.root().name
        if not root_name.startswith("homeassistant.components."):
            return

        parts = root_name.split(".")
        current_module = parts[3] if len(parts) > 3 else ""
        if current_module in _SKIP_MODULES:
            return

        # Only flag integrations that have a config flow (and thus can use
        # entry.runtime_data). YAML-only integrations legitimately need
        # hass.data[DOMAIN].
        integration = parts[2]
        if not _has_config_flow(integration, node.root()):
            return

        func = _enclosing_function(node)
        if func and func.name in _SKIP_FUNCTIONS:
            return

        # Don't flag deletion: del hass.data[DOMAIN] or hass.data[DOMAIN].pop(...)
        parent = node.parent
        if isinstance(parent, nodes.Delete):
            return
        if (
            isinstance(parent, nodes.Attribute)
            and parent.attrname == "pop"
            and isinstance(parent.parent, nodes.Call)
        ):
            return

        self.add_message("hass-use-runtime-data", node=node)