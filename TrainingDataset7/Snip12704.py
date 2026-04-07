def pretty_name(name):
    """Convert 'first_name' to 'First name'."""
    if not name:
        return ""
    return name.replace("_", " ").capitalize()