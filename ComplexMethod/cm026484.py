def interfaces(self) -> Generator[AlexaCapability]:
        """Yield the supported interfaces."""
        sensor_type = self.get_type()
        if sensor_type is self.TYPE_CONTACT:
            yield AlexaContactSensor(self.hass, self.entity)
        elif sensor_type is self.TYPE_MOTION:
            yield AlexaMotionSensor(self.hass, self.entity)
        elif sensor_type is self.TYPE_PRESENCE:
            yield AlexaEventDetectionSensor(self.hass, self.entity)

        # yield additional interfaces based on specified display category in config.
        entity_conf = self.config.entity_config.get(self.entity.entity_id, {})
        if CONF_DISPLAY_CATEGORIES in entity_conf:
            if entity_conf[CONF_DISPLAY_CATEGORIES] == DisplayCategory.DOORBELL:
                yield AlexaDoorbellEventSource(self.entity)
            elif entity_conf[CONF_DISPLAY_CATEGORIES] == DisplayCategory.CONTACT_SENSOR:
                yield AlexaContactSensor(self.hass, self.entity)
            elif entity_conf[CONF_DISPLAY_CATEGORIES] == DisplayCategory.MOTION_SENSOR:
                yield AlexaMotionSensor(self.hass, self.entity)
            elif entity_conf[CONF_DISPLAY_CATEGORIES] == DisplayCategory.CAMERA:
                yield AlexaEventDetectionSensor(self.hass, self.entity)

        yield AlexaEndpointHealth(self.hass, self.entity)
        yield Alexa(self.entity)