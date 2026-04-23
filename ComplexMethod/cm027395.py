async def _async_setup_cloudhook(
    hass: HomeAssistant,
    entry: ConfigEntry,
    user_id: str,
    webhook_id: str,
) -> None:
    """Set up cloudhook forwarding for a mobile_app entry."""
    local_only = await async_is_local_only_user(hass, user_id)

    def clean_cloudhook() -> None:
        """Clean up cloudhook from config entry."""
        if CONF_CLOUDHOOK_URL in entry.data:
            data = dict(entry.data)
            data.pop(CONF_CLOUDHOOK_URL)
            hass.config_entries.async_update_entry(entry, data=data)

    if local_only:
        # Local-only user should not have a cloudhook
        if cloud.async_is_logged_in(hass) and CONF_CLOUDHOOK_URL in entry.data:
            with suppress(cloud.CloudNotAvailable, ValueError):
                await cloud.async_delete_cloudhook(hass, webhook_id)
        clean_cloudhook()
        return

    def on_cloudhook_change(cloudhook: dict[str, Any] | None) -> None:
        """Handle cloudhook changes."""
        if cloudhook:
            if entry.data.get(CONF_CLOUDHOOK_URL) == cloudhook[CONF_CLOUDHOOK_URL]:
                return

            hass.config_entries.async_update_entry(
                entry,
                data={**entry.data, CONF_CLOUDHOOK_URL: cloudhook[CONF_CLOUDHOOK_URL]},
            )
        else:
            clean_cloudhook()

    async def manage_cloudhook(state: cloud.CloudConnectionState) -> None:
        if (
            state is cloud.CloudConnectionState.CLOUD_CONNECTED
            and CONF_CLOUDHOOK_URL not in entry.data
        ):
            await async_create_cloud_hook(hass, webhook_id, entry)
        elif (
            state is cloud.CloudConnectionState.CLOUD_DISCONNECTED
            and not cloud.async_is_logged_in(hass)
        ):
            clean_cloudhook()

    entry.async_on_unload(
        cloud.async_listen_cloudhook_change(hass, webhook_id, on_cloudhook_change)
    )

    if cloud.async_is_logged_in(hass):
        if (
            CONF_CLOUDHOOK_URL not in entry.data
            and cloud.async_active_subscription(hass)
            and cloud.async_is_connected(hass)
        ):
            await async_create_cloud_hook(hass, webhook_id, entry)
    elif CONF_CLOUDHOOK_URL in entry.data:
        # If we have a cloudhook but no longer logged in to the cloud, remove it from the entry
        clean_cloudhook()

    entry.async_on_unload(cloud.async_listen_connection_change(hass, manage_cloudhook))