def _tx_resource_for_name(name):
    """Return the Transifex resource name."""
    return "django." + _tx_resource_slug_for_name(name)