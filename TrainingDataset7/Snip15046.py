def _tx_resource_slug_for_name(name):
    """Return the Transifex resource slug for the given name."""
    if name != "core":
        name = f"contrib-{name}"
    return name