def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the client wrapper."""
        self.hass = hass
        self.config_entry = entry

        host = entry.data[CONF_HOST]
        port = entry.data[CONF_PORT]

        # Make sure we initialize the Satel controller with the configured entries to monitor
        partitions = [
            subentry.data[CONF_PARTITION_NUMBER]
            for subentry in entry.subentries.values()
            if subentry.subentry_type == SUBENTRY_TYPE_PARTITION
        ]

        zones = [
            subentry.data[CONF_ZONE_NUMBER]
            for subentry in entry.subentries.values()
            if subentry.subentry_type == SUBENTRY_TYPE_ZONE
        ]

        outputs = [
            subentry.data[CONF_OUTPUT_NUMBER]
            for subentry in entry.subentries.values()
            if subentry.subentry_type == SUBENTRY_TYPE_OUTPUT
        ]

        switchable_outputs = [
            subentry.data[CONF_SWITCHABLE_OUTPUT_NUMBER]
            for subentry in entry.subentries.values()
            if subentry.subentry_type == SUBENTRY_TYPE_SWITCHABLE_OUTPUT
        ]

        monitored_outputs = outputs + switchable_outputs

        self.controller = AsyncSatel(
            host,
            port,
            zones,
            monitored_outputs,
            partitions,
            integration_key=entry.data[CONF_ENCRYPTION_KEY],
        )