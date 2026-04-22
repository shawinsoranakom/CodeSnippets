def get_fqn_type(obj: object) -> str:
    """Get module.type_name for a given object."""
    return get_fqn(type(obj))