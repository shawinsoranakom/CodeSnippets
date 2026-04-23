def _manage_distributed_env(request: FixtureRequest, monkeypatch: MonkeyPatch) -> None:
    """Set environment variables for distributed tests if specific devices are requested."""
    env_key = _get_visible_devices_env()
    if not env_key:
        return

    # Save old environment for logic checks, monkeypatch handles restoration
    old_value = os.environ.get(env_key)

    marker = request.node.get_closest_marker("require_distributed")
    if marker:  # distributed test
        required = marker.args[0] if marker.args else 2
        specific_devices = marker.args[1] if len(marker.args) > 1 else None

        if specific_devices:
            devices_str = ",".join(map(str, specific_devices))
        else:
            devices_str = ",".join(str(i) for i in range(required))

        monkeypatch.setenv(env_key, devices_str)
        monkeypatch.syspath_prepend(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    else:  # non-distributed test
        if old_value:
            visible_devices = [v for v in old_value.split(",") if v != ""]
            monkeypatch.setenv(env_key, visible_devices[0] if visible_devices else "0")
        else:
            monkeypatch.setenv(env_key, "0")

        if CURRENT_DEVICE == "cuda":
            monkeypatch.setattr(torch.cuda, "device_count", lambda: 1)
        elif CURRENT_DEVICE == "npu":
            monkeypatch.setattr(torch.npu, "device_count", lambda: 1)