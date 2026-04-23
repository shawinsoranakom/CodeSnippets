def _entities_for_device[
        _E: CoordinatedTPLinkFeatureEntity,
        _D: TPLinkFeatureEntityDescription,
    ](
        cls,
        hass: HomeAssistant,
        device: Device,
        coordinator: TPLinkDataUpdateCoordinator,
        *,
        feature_type: Feature.Type,
        entity_class: type[_E],
        descriptions: Mapping[str, _D],
        platform_domain: str,
        parent: Device | None = None,
    ) -> list[_E]:
        """Return a list of entities to add.

        This filters out unwanted features to avoid creating unnecessary entities
        for device features that are implemented by specialized platforms like light.
        """
        entities: list[_E] = [
            entity_class(
                device,
                coordinator,
                feature=feat,
                description=desc,
                parent=parent,
            )
            for feat in device.features.values()
            if feat.type == feature_type
            and feat.id not in EXCLUDED_FEATURES
            and (
                feat.category is not Feature.Category.Primary
                or device.device_type not in DEVICETYPES_WITH_SPECIALIZED_PLATFORMS
                or feat.id in FEATURES_ALLOW_LIST
            )
            and (
                desc := cls._description_for_feature(
                    feat, descriptions, device=device, parent=parent
                )
            )
            and async_check_create_deprecated(
                hass,
                cls._get_feature_unique_id(device, desc),
                desc,
            )
        ]
        async_process_deprecated(
            hass, platform_domain, coordinator.config_entry.entry_id, entities, device
        )
        return entities