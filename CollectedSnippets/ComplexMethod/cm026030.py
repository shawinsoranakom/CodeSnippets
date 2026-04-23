def async_setup_device_entities(
        device_address: dict[str, EheimDigitalDevice],
    ) -> None:
        """Set up the number entities for one or multiple devices."""
        entities: list[EheimDigitalNumber[Any]] = []
        for device in device_address.values():
            if isinstance(device, EheimDigitalClassicVario):
                entities.extend(
                    EheimDigitalNumber[EheimDigitalClassicVario](
                        coordinator, device, description
                    )
                    for description in CLASSICVARIO_DESCRIPTIONS
                )
            if isinstance(device, EheimDigitalFilter):
                entities.extend(
                    EheimDigitalNumber[EheimDigitalFilter](
                        coordinator, device, description
                    )
                    for description in FILTER_DESCRIPTIONS
                )
            if isinstance(device, EheimDigitalHeater):
                entities.extend(
                    EheimDigitalNumber[EheimDigitalHeater](
                        coordinator, device, description
                    )
                    for description in HEATER_DESCRIPTIONS
                )
            if isinstance(device, EheimDigitalReeflexUV):
                entities.extend(
                    EheimDigitalNumber[EheimDigitalReeflexUV](
                        coordinator, device, description
                    )
                    for description in REEFLEX_DESCRIPTIONS
                )
            entities.extend(
                EheimDigitalNumber[EheimDigitalDevice](coordinator, device, description)
                for description in GENERAL_DESCRIPTIONS
            )

        async_add_entities(entities)