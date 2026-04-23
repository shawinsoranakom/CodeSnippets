async def async_parse_messages(self, messages) -> None:
        """Parse notification message."""
        unique_id = self.unique_id
        assert unique_id is not None
        for msg in messages:
            # Guard against empty message
            if not msg.Topic:
                continue

            # Topic may look like the following
            #
            # tns1:RuleEngine/CellMotionDetector/Motion//.
            # tns1:RuleEngine/CellMotionDetector/Motion
            # tns1:RuleEngine/CellMotionDetector/Motion/
            # tns1:UserAlarm/IVA/HumanShapeDetect
            #
            # Our parser expects the topic to be
            # tns1:RuleEngine/CellMotionDetector/Motion
            topic = msg.Topic._value_1.rstrip("/.")  # noqa: SLF001

            try:
                events = await onvif_parsers.parse(topic, unique_id, msg)
                error = None
            except onvif_parsers.errors.UnknownTopicError:
                if topic not in UNHANDLED_TOPICS:
                    LOGGER.warning(
                        "%s: No registered handler for event from %s: %s",
                        self.name,
                        unique_id,
                        onvif_parsers.util.event_to_debug_format(msg),
                    )
                    UNHANDLED_TOPICS.add(topic)
                continue
            except (AttributeError, KeyError) as e:
                events = []
                error = e

            if not events:
                LOGGER.warning(
                    "%s: Unable to parse event from %s: %s: %s",
                    self.name,
                    unique_id,
                    error,
                    onvif_parsers.util.event_to_debug_format(msg),
                )
                continue

            for event in events:
                value = event.value
                if event.device_class == "timestamp" and isinstance(value, str):
                    value = _local_datetime_or_none(value)

                ha_event = Event(
                    uid=event.uid,
                    name=event.name,
                    platform=event.platform,
                    device_class=event.device_class,
                    unit_of_measurement=event.unit_of_measurement,
                    value=value,
                    entity_category=ENTITY_CATEGORY_MAPPING.get(
                        event.entity_category or ""
                    ),
                    entity_enabled=event.entity_enabled,
                )
                self.get_uids_by_platform(ha_event.platform).add(ha_event.uid)
                self._events[ha_event.uid] = ha_event