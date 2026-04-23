def __init__(self, entity_data: EntityData, **kwargs: Any) -> None:
        """Initialize the ZHA select entity."""
        super().__init__(entity_data, **kwargs)
        entity = self.entity_data.entity

        if entity.device_class is not None:
            self._attr_device_class = SensorDeviceClass(entity.device_class)

        if entity.state_class is not None:
            self._attr_state_class = SensorStateClass(entity.state_class)

        if hasattr(entity.info_object, "unit") and entity.info_object.unit is not None:
            self._attr_native_unit_of_measurement = entity.info_object.unit

        if (
            hasattr(entity, "entity_description")
            and entity.entity_description is not None
        ):
            entity_description = entity.entity_description

            if entity_description.state_class is not None:
                self._attr_state_class = SensorStateClass(
                    entity_description.state_class.value
                )

            if entity_description.scale is not None:
                self._attr_scale = entity_description.scale

            if entity_description.native_unit_of_measurement is not None:
                self._attr_native_unit_of_measurement = (
                    entity_description.native_unit_of_measurement
                )

            if entity_description.device_class is not None:
                self._attr_device_class = SensorDeviceClass(
                    entity_description.device_class.value
                )

        if entity.info_object.suggested_display_precision is not None:
            self._attr_suggested_display_precision = (
                entity.info_object.suggested_display_precision
            )