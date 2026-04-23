def async_setup_device_entities(
        device_address: dict[str, EheimDigitalDevice],
    ) -> None:
        """Set up the number entities for one or multiple devices."""
        entities: list[EheimDigitalSelect[Any]] = []
        for device in device_address.values():
            if isinstance(device, EheimDigitalClassicVario):
                entities.extend(
                    EheimDigitalSelect[EheimDigitalClassicVario](
                        coordinator, device, description
                    )
                    for description in CLASSICVARIO_DESCRIPTIONS
                )
            if isinstance(device, EheimDigitalFilter):
                entities.extend(
                    EheimDigitalFilterSelect(coordinator, device, description)
                    for description in FILTER_DESCRIPTIONS
                )
            if isinstance(device, EheimDigitalReeflexUV):
                entities.extend(
                    EheimDigitalSelect[EheimDigitalReeflexUV](
                        coordinator, device, description
                    )
                    for description in REEFLEX_DESCRIPTIONS
                )

        async_add_entities(entities)