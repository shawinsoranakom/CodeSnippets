def async_setup_device_entities(
        device_address: dict[str, EheimDigitalDevice],
    ) -> None:
        """Set up the time entities for one or multiple devices."""
        entities: list[EheimDigitalTime[Any]] = []
        for device in device_address.values():
            if isinstance(device, EheimDigitalFilter):
                entities.extend(
                    EheimDigitalTime[EheimDigitalFilter](
                        coordinator, device, description
                    )
                    for description in FILTER_DESCRIPTIONS
                )
            if isinstance(device, EheimDigitalClassicVario):
                entities.extend(
                    EheimDigitalTime[EheimDigitalClassicVario](
                        coordinator, device, description
                    )
                    for description in CLASSICVARIO_DESCRIPTIONS
                )
            if isinstance(device, EheimDigitalHeater):
                entities.extend(
                    EheimDigitalTime[EheimDigitalHeater](
                        coordinator, device, description
                    )
                    for description in HEATER_DESCRIPTIONS
                )
            if isinstance(device, EheimDigitalReeflexUV):
                entities.extend(
                    EheimDigitalTime[EheimDigitalReeflexUV](
                        coordinator, device, description
                    )
                    for description in REEFLEX_DESCRIPTIONS
                )

        async_add_entities(entities)