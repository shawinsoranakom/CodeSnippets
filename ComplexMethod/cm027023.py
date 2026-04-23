async def async_register_panel(
    hass: HomeAssistant,
    # The url to serve the panel
    frontend_url_path: str,
    # The webcomponent name that loads your panel
    webcomponent_name: str,
    # Title/icon for sidebar
    sidebar_title: str | None = None,
    sidebar_icon: str | None = None,
    # JS source of your panel
    js_url: str | None = None,
    # JS module of your panel
    module_url: str | None = None,
    # If your panel should be run inside an iframe
    embed_iframe: bool = DEFAULT_EMBED_IFRAME,
    # Should user be asked for confirmation when loading external source
    trust_external: bool = DEFAULT_TRUST_EXTERNAL,
    # Configuration to be passed to the panel
    config: ConfigType | None = None,
    # If your panel should only be shown to admin users
    require_admin: bool = False,
    # If your panel is used to configure an integration, needs the domain of the integration
    config_panel_domain: str | None = None,
) -> None:
    """Register a new custom panel."""
    if js_url is None and module_url is None:
        raise ValueError("Either js_url, module_url or html_url is required.")
    if config is not None and not isinstance(config, dict):
        raise ValueError("Config needs to be a dictionary.")

    custom_panel_config = {
        "name": webcomponent_name,
        "embed_iframe": embed_iframe,
        "trust_external": trust_external,
    }

    if js_url is not None:
        custom_panel_config["js_url"] = js_url

    if module_url is not None:
        custom_panel_config["module_url"] = module_url

    if config is not None:
        # Make copy because we're mutating it
        config = dict(config)
    else:
        config = {}

    config["_panel_custom"] = custom_panel_config

    frontend.async_register_built_in_panel(
        hass,
        component_name="custom",
        sidebar_title=sidebar_title,
        sidebar_icon=sidebar_icon,
        frontend_url_path=frontend_url_path,
        config=config,
        require_admin=require_admin,
        config_panel_domain=config_panel_domain,
    )