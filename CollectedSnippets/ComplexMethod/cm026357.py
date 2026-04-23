async def _async_setup_themes(
    hass: HomeAssistant, themes: dict[str, Any] | None
) -> None:
    """Set up themes data and services."""
    hass.data[DATA_THEMES] = themes or {}

    store = hass.data[DATA_THEMES_STORE] = Store(
        hass, THEMES_STORAGE_VERSION, THEMES_STORAGE_KEY
    )

    if not (theme_data := await store.async_load()) or not isinstance(theme_data, dict):
        theme_data = {}
    theme_name = theme_data.get(DATA_DEFAULT_THEME, DEFAULT_THEME)
    dark_theme_name = theme_data.get(DATA_DEFAULT_DARK_THEME)

    if theme_name == DEFAULT_THEME or theme_name in hass.data[DATA_THEMES]:
        hass.data[DATA_DEFAULT_THEME] = theme_name
    else:
        hass.data[DATA_DEFAULT_THEME] = DEFAULT_THEME

    if dark_theme_name == DEFAULT_THEME or dark_theme_name in hass.data[DATA_THEMES]:
        hass.data[DATA_DEFAULT_DARK_THEME] = dark_theme_name

    @callback
    def update_theme_and_fire_event() -> None:
        """Update theme_color in manifest."""
        name = hass.data[DATA_DEFAULT_THEME]
        themes = hass.data[DATA_THEMES]
        if name != DEFAULT_THEME:
            MANIFEST_JSON.update_key(
                "theme_color",
                themes[name].get(
                    "app-header-background-color",
                    themes[name].get(PRIMARY_COLOR, DEFAULT_THEME_COLOR),
                ),
            )
        else:
            MANIFEST_JSON.update_key("theme_color", DEFAULT_THEME_COLOR)
        hass.bus.async_fire(EVENT_THEMES_UPDATED)

    @callback
    def set_theme(call: ServiceCall) -> None:
        """Set backend-preferred theme."""

        def _update_hass_theme(theme: str, light: bool) -> None:
            theme_key = DATA_DEFAULT_THEME if light else DATA_DEFAULT_DARK_THEME
            if theme == VALUE_NO_THEME:
                to_set = DEFAULT_THEME if light else None
            else:
                _LOGGER.info(
                    "Theme %s set as default %s theme",
                    theme,
                    "light" if light else "dark",
                )
                to_set = theme
            hass.data[theme_key] = to_set

        name = call.data.get(CONF_NAME)
        if name is not None and CONF_MODE in call.data:
            mode = call.data.get("mode", "light")
            light_mode = mode == "light"
            _update_hass_theme(name, light_mode)
        else:
            name_dark = call.data.get(CONF_NAME_DARK)
            if name:
                _update_hass_theme(name, True)
            if name_dark:
                _update_hass_theme(name_dark, False)

        store.async_delay_save(
            lambda: {
                DATA_DEFAULT_THEME: hass.data[DATA_DEFAULT_THEME],
                DATA_DEFAULT_DARK_THEME: hass.data.get(DATA_DEFAULT_DARK_THEME),
            },
            THEMES_SAVE_DELAY,
        )
        update_theme_and_fire_event()

    async def reload_themes(_: ServiceCall) -> None:
        """Reload themes."""
        config = await async_hass_config_yaml(hass)
        new_themes = config.get(DOMAIN, {}).get(CONF_THEMES, {})

        try:
            new_themes = _validate_themes(new_themes)
        except vol.Invalid as err:
            raise HomeAssistantError(f"Failed to reload themes: {err}") from err

        hass.data[DATA_THEMES] = new_themes
        if hass.data[DATA_DEFAULT_THEME] not in new_themes:
            hass.data[DATA_DEFAULT_THEME] = DEFAULT_THEME
        if (
            hass.data.get(DATA_DEFAULT_DARK_THEME)
            and hass.data.get(DATA_DEFAULT_DARK_THEME) not in new_themes
        ):
            hass.data[DATA_DEFAULT_DARK_THEME] = None
        update_theme_and_fire_event()

    service.async_register_admin_service(
        hass,
        DOMAIN,
        SERVICE_SET_THEME,
        set_theme,
        vol.All(
            {
                vol.Optional(CONF_NAME): _validate_selected_theme,
                vol.Exclusive(CONF_NAME_DARK, "dark_modes"): _validate_selected_theme,
                vol.Exclusive(CONF_MODE, "dark_modes"): vol.Any("dark", "light"),
            },
            cv.has_at_least_one_key(CONF_NAME, CONF_NAME_DARK),
        ),
    )

    service.async_register_admin_service(
        hass, DOMAIN, SERVICE_RELOAD_THEMES, reload_themes
    )