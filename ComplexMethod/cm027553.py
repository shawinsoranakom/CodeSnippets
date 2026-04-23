def _async_normalize_config_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Move options from data for imported entries.

    Initialize options with default values for other entries.

    Copy the unique id to CONF_ID if it is missing
    """
    if not entry.options:
        hass.config_entries.async_update_entry(
            entry,
            data={
                CONF_HOST: entry.data.get(CONF_HOST),
                CONF_ID: entry.data.get(CONF_ID) or entry.unique_id,
                CONF_DETECTED_MODEL: entry.data.get(CONF_DETECTED_MODEL),
            },
            options={
                CONF_NAME: entry.data.get(CONF_NAME, ""),
                CONF_MODEL: entry.data.get(
                    CONF_MODEL, entry.data.get(CONF_DETECTED_MODEL, "")
                ),
                CONF_TRANSITION: entry.data.get(CONF_TRANSITION, DEFAULT_TRANSITION),
                CONF_MODE_MUSIC: entry.data.get(CONF_MODE_MUSIC, DEFAULT_MODE_MUSIC),
                CONF_SAVE_ON_CHANGE: entry.data.get(
                    CONF_SAVE_ON_CHANGE, DEFAULT_SAVE_ON_CHANGE
                ),
                CONF_NIGHTLIGHT_SWITCH: entry.data.get(
                    CONF_NIGHTLIGHT_SWITCH, DEFAULT_NIGHTLIGHT_SWITCH
                ),
            },
            unique_id=entry.unique_id or entry.data.get(CONF_ID),
        )
    elif entry.unique_id and not entry.data.get(CONF_ID):
        hass.config_entries.async_update_entry(
            entry,
            data={CONF_HOST: entry.data.get(CONF_HOST), CONF_ID: entry.unique_id},
        )
    elif entry.data.get(CONF_ID) and not entry.unique_id:
        hass.config_entries.async_update_entry(
            entry,
            unique_id=entry.data[CONF_ID],
        )