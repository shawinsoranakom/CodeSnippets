def get_rpc_key_instances(
    keys_dict: dict[str, Any], key: str, all_lights: bool = False
) -> list[str]:
    """Return list of key instances for RPC device from a dict."""
    if key in keys_dict:
        return [key]

    if key == "switch" and "cover:0" in keys_dict:
        key = "cover"

    if key in All_LIGHT_TYPES and all_lights:
        return [k for k in keys_dict if k.startswith(All_LIGHT_TYPES)]

    return [k for k in keys_dict if k.startswith(f"{key}:")]