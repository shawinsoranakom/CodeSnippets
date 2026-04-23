def check(config_dir, secrets=False):
    """Perform a check by mocking hass load functions."""
    logging.getLogger("homeassistant.loader").setLevel(logging.CRITICAL)
    res: dict[str, Any] = {
        "yaml_files": OrderedDict(),  # yaml_files loaded
        "secrets": OrderedDict(),  # secret cache and secrets loaded
        "except": OrderedDict(),  # critical exceptions raised (with config)
        "warn": OrderedDict(),  # non critical exceptions raised (with config)
        #'components' is a HomeAssistantConfig
        "secret_cache": {},
    }

    # pylint: disable-next=possibly-unused-variable
    def mock_load(filename, secrets=None):
        """Mock hass.util.load_yaml to save config file names."""
        res["yaml_files"][filename] = True
        return MOCKS["load"][1](filename, secrets)

    # pylint: disable-next=possibly-unused-variable
    def mock_secrets(ldr, node):
        """Mock _get_secrets."""
        try:
            val = MOCKS["secrets"][1](ldr, node)
        except HomeAssistantError:
            val = None
        res["secrets"][node.value] = val
        return val

    # Patches with local mock functions
    for key, val in MOCKS.items():
        if not secrets and key == "secrets":
            continue
        # The * in the key is removed to find the mock_function (side_effect)
        # This allows us to use one side_effect to patch multiple locations
        mock_function = locals()[f"mock_{key.replace('*', '')}"]
        PATCHES[key] = patch(val[0], side_effect=mock_function)

    # Start all patches
    for pat in PATCHES.values():
        pat.start()

    if secrets:
        # Ensure !secrets point to the patched function
        yaml_loader.add_constructor("!secret", yaml_loader.secret_yaml)

    def secrets_proxy(*args):
        secrets = Secrets(*args)
        res["secret_cache"] = secrets._cache  # noqa: SLF001
        return secrets

    try:
        with patch.object(yaml_loader, "Secrets", secrets_proxy):
            res["components"] = asyncio.run(async_check_config(config_dir))
        res["secret_cache"] = {
            str(key): val for key, val in res["secret_cache"].items()
        }
        for err in res["components"].errors:
            domain = err.domain or ERROR_STR
            res["except"].setdefault(domain, []).append(err.message)
            if err.config:
                res["except"].setdefault(domain, []).append(err.config)

        for err in res["components"].warnings:
            domain = err.domain or WARNING_STR
            res["warn"].setdefault(domain, []).append(err.message)
            if err.config:
                res["warn"].setdefault(domain, []).append(err.config)

    except Exception as err:  # noqa: BLE001
        print(color("red", "Fatal error while loading config:"), str(err))
        res["except"].setdefault(ERROR_STR, []).append(str(err))
    finally:
        # Stop all patches
        for pat in PATCHES.values():
            pat.stop()
        if secrets:
            # Ensure !secrets point to the original function
            yaml_loader.add_constructor("!secret", yaml_loader.secret_yaml)

    return res