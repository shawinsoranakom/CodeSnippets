def _apply_entities_changes(state_dict: dict, change_dict: dict) -> None:
    """Apply a diff set to a dict.

    Port of the client side merging
    """
    additions = change_dict.get("+", {})
    if "lc" in additions:
        additions["lu"] = additions["lc"]
    if attributes := additions.pop("a", None):
        state_dict["attributes"].update(attributes)
    if context := additions.pop("c", None):
        if isinstance(context, str):
            state_dict["context"]["id"] = context
        else:
            state_dict["context"].update(context)
    for k, v in additions.items():
        state_dict[STATE_KEY_LONG_NAMES[k]] = v
    for key, items in change_dict.get("-", {}).items():
        for item in items:
            del state_dict[STATE_KEY_LONG_NAMES[key]][item]