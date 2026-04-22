def server_option_changed(
    old_options: Dict[str, ConfigOption], new_options: Dict[str, ConfigOption]
) -> bool:
    """Return True if and only if an option in the server section differs
    between old_options and new_options."""
    for opt_name in old_options.keys():
        if not opt_name.startswith("server"):
            continue

        old_val = old_options[opt_name].value
        new_val = new_options[opt_name].value
        if old_val != new_val:
            return True

    return False