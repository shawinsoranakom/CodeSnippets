def _is_hass_data_domain_access(node: nodes.Subscript) -> bool:
    """Return True if node is hass.data[DOMAIN] or self.hass.data[DOMAIN]."""
    if not isinstance(node.value, nodes.Attribute):
        return False
    if node.value.attrname != "data":
        return False

    slice_node = node.slice
    if not isinstance(slice_node, nodes.Name) or slice_node.name != "DOMAIN":
        return False

    expr = node.value.expr
    if isinstance(expr, nodes.Name) and expr.name == "hass":
        return True
    return (
        isinstance(expr, nodes.Attribute)
        and expr.attrname == "hass"
        and isinstance(expr.expr, nodes.Name)
        and expr.expr.name == "self"
    )