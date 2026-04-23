def _validate_integration(config: Config, integration: Integration) -> None:
    """Validate config flow of an integration."""
    config_flow_file = integration.path / "config_flow.py"

    if not config_flow_file.is_file():
        if integration.manifest.get("config_flow"):
            integration.add_error(
                "config_flow",
                "Config flows need to be defined in the file config_flow.py",
            )
        return

    config_flow = config_flow_file.read_text()

    needs_unique_id = integration.domain not in UNIQUE_ID_IGNORE and (
        "async_step_discovery" in config_flow
        or "async_step_bluetooth" in config_flow
        or "async_step_hassio" in config_flow
        or "async_step_homekit" in config_flow
        or "async_step_mqtt" in config_flow
        or "async_step_ssdp" in config_flow
        or "async_step_zeroconf" in config_flow
        or "async_step_dhcp" in config_flow
        or "async_step_usb" in config_flow
    )

    if not needs_unique_id:
        return

    has_unique_id = (
        "self.async_set_unique_id" in config_flow
        or "self._async_handle_discovery_without_unique_id" in config_flow
        or "register_discovery_flow" in config_flow
        or "AbstractOAuth2FlowHandler" in config_flow
    )

    if has_unique_id:
        return

    if config.specific_integrations:
        notice_method = integration.add_warning
    else:
        notice_method = integration.add_error

    notice_method(
        "config_flow", "Config flows that are discoverable need to set a unique ID"
    )