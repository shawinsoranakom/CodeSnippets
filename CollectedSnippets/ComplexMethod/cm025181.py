def event(self, message_body) -> None:
        """Handle events from pysml."""
        assert isinstance(message_body, SmlGetListResponse)
        LOGGER.debug("Received sml message on %s: %s", self._serial_port, message_body)

        electricity_id = message_body["serverId"]

        if electricity_id is None:
            LOGGER.debug(
                "No electricity id found in sml message on %s", self._serial_port
            )
            return
        electricity_id = electricity_id.replace(" ", "")

        new_entities: list[EDL21Entity] = []
        for telegram in message_body.get("valList", []):
            if not (obis := telegram.get("objName")):
                continue

            if (electricity_id, obis) in self._registered_obis:
                async_dispatcher_send(
                    self._hass, SIGNAL_EDL21_TELEGRAM, electricity_id, telegram
                )
            else:
                entity_description = SENSORS.get(obis)
                if entity_description:
                    new_entities.append(
                        EDL21Entity(
                            electricity_id,
                            obis,
                            entity_description,
                            telegram,
                        )
                    )
                    self._registered_obis.add((electricity_id, obis))
                elif obis not in self._OBIS_BLACKLIST:
                    LOGGER.warning(
                        "Unhandled sensor %s detected. Please report at %s",
                        obis,
                        "https://github.com/home-assistant/core/issues?q=is%3Aopen+is%3Aissue+label%3A%22integration%3A+edl21%22",
                    )
                    self._OBIS_BLACKLIST.add(obis)

        if new_entities:
            self._async_add_entities(new_entities, update_before_add=True)