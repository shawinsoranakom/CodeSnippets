async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version == 1:
        # Version 1 had states as first-class selections
        # Version 2 only allows states w/o districts, districts and communities
        region_id = config_entry.data[CONF_REGION]

        websession = async_get_clientsession(hass)
        try:
            regions_data = await Client(websession).get_regions()
        except (aiohttp.ClientError, TimeoutError) as err:
            _LOGGER.warning(
                "Could not migrate config entry %s: failed to fetch current regions: %s",
                config_entry.entry_id,
                err,
            )
            return False

        if TYPE_CHECKING:
            assert isinstance(regions_data, dict)

        state_with_districts = None
        for state in regions_data["states"]:
            if state["regionId"] == region_id and state.get("regionChildIds"):
                state_with_districts = state
                break

        if state_with_districts:
            ir.async_create_issue(
                hass,
                DOMAIN,
                f"deprecated_state_region_{config_entry.entry_id}",
                is_fixable=False,
                issue_domain=DOMAIN,
                severity=ir.IssueSeverity.WARNING,
                translation_key="deprecated_state_region",
                translation_placeholders={
                    "region_name": config_entry.data.get(CONF_NAME, region_id),
                },
            )

            return False

        hass.config_entries.async_update_entry(config_entry, version=2)
        _LOGGER.info("Migration to version %s successful", 2)
        return True

    _LOGGER.error("Unknown version %s", config_entry.version)
    return False