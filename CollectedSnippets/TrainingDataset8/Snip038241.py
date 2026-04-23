def get_fqn(the_type: type) -> str:
    """Get module.type_name for a given type."""
    return f"{the_type.__module__}.{the_type.__qualname__}"