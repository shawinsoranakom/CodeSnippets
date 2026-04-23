def _handle_device_visibility(items: list[Item]):
    """Handle device visibility based on test markers."""
    env_key = _get_visible_devices_env()
    if env_key is None or CURRENT_DEVICE in ("cpu", "mps"):
        return

    # Parse visible devices
    visible_devices_env = os.environ.get(env_key)
    if visible_devices_env is None:
        available = get_device_count()
    else:
        visible_devices = [v for v in visible_devices_env.split(",") if v != ""]
        available = len(visible_devices)

    for item in items:
        marker = item.get_closest_marker("require_distributed")
        if not marker:
            continue

        required = marker.args[0] if marker.args else 2
        if available < required:
            item.add_marker(pytest.mark.skip(reason=f"test requires {required} devices, but only {available} visible"))