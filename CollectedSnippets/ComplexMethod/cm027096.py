async def async_device_discovered(payload: dict, mac: str) -> None:
        """Process the received message."""

        if ALREADY_DISCOVERED not in hass.data:
            # Discovery is shutting down
            return

        _LOGGER.debug("Received discovery data for tasmota device: %s", mac)
        tasmota_device_config = tasmota_get_device_config(payload)
        await setup_device(tasmota_device_config, mac)

        hass.data[DISCOVERY_DATA][mac] = payload

        add_entities = True

        command_topic = get_topic_command(payload) if payload else None
        state_topic = get_topic_stat(payload) if payload else None

        # Create or clear issue if topic is missing prefix
        issue_id = f"topic_no_prefix_{mac}"
        if payload and command_topic == state_topic:
            _LOGGER.warning(
                "Tasmota device '%s' with IP %s doesn't set %%prefix%% in its topic",
                tasmota_device_config[tasmota_const.CONF_NAME],
                tasmota_device_config[tasmota_const.CONF_IP],
            )
            ir.async_create_issue(
                hass,
                DOMAIN,
                issue_id,
                data={"key": "topic_no_prefix"},
                is_fixable=False,
                learn_more_url=MQTT_TOPIC_URL,
                severity=ir.IssueSeverity.ERROR,
                translation_key="topic_no_prefix",
                translation_placeholders={
                    "name": tasmota_device_config[tasmota_const.CONF_NAME],
                    "ip": tasmota_device_config[tasmota_const.CONF_IP],
                },
            )
            add_entities = False
        else:
            ir.async_delete_issue(hass, DOMAIN, issue_id)

        # Clear previous issues caused by duplicated topic
        issue_reg = ir.async_get(hass)
        tasmota_issues = [
            issue for key, issue in issue_reg.issues.items() if key[0] == DOMAIN
        ]
        for issue in tasmota_issues:
            if issue.data and issue.data["key"] == "topic_duplicated":
                issue_data: DuplicatedTopicIssueData = cast(
                    DuplicatedTopicIssueData, issue.data
                )
                macs = issue_data["mac"].split()
                if mac not in macs:
                    continue
                if payload and command_topic == issue_data["topic"]:
                    continue
                if len(macs) > 2:
                    # This device is no longer duplicated, update the issue
                    warn_if_topic_duplicated(hass, issue_data["topic"], None, {})
                    continue
                ir.async_delete_issue(hass, DOMAIN, issue.issue_id)

        if not payload:
            return
        assert isinstance(command_topic, str)

        # Warn and add issues if there are duplicated topics
        if warn_if_topic_duplicated(hass, command_topic, mac, tasmota_device_config):
            add_entities = False

        if not add_entities:
            # Add the device entry so the user can identify the device, but do not add
            # entities or triggers
            return

        tasmota_triggers = tasmota_get_triggers(payload)
        for trigger_config in tasmota_triggers:
            discovery_hash: DiscoveryHashType = (
                mac,
                "automation",
                "trigger",
                trigger_config.trigger_id,
            )
            if discovery_hash in hass.data[ALREADY_DISCOVERED]:
                _LOGGER.debug(
                    "Trigger already added, sending update: %s",
                    discovery_hash,
                )
                async_dispatcher_send(
                    hass,
                    TASMOTA_DISCOVERY_ENTITY_UPDATED.format(*discovery_hash),
                    trigger_config,
                )
            elif trigger_config.is_active:
                _LOGGER.debug("Adding new trigger: %s", discovery_hash)
                hass.data[ALREADY_DISCOVERED][discovery_hash] = None

                tasmota_trigger = tasmota_get_trigger(trigger_config, tasmota_mqtt)

                async_dispatcher_send(
                    hass,
                    TASMOTA_DISCOVERY_ENTITY_NEW.format("device_automation"),
                    tasmota_trigger,
                    discovery_hash,
                )

        for platform in PLATFORMS:
            tasmota_entities = tasmota_get_entities_for_platform(payload, platform)
            for tasmota_entity_config, discovery_hash in tasmota_entities:
                _discover_entity(tasmota_entity_config, discovery_hash, platform)