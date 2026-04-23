def update_lights():
        """Update the lights objects with the latest info from the bridge."""
        try:
            new_lights = bridge.update_all_light_status(
                config[CONF_INTERVAL_LIGHTIFY_STATUS]
            )
            lights_changed = bridge.lights_changed()
        except TimeoutError:
            _LOGGER.error("Timeout during updating of lights")
            return 0
        except OSError:
            _LOGGER.error("OSError during updating of lights")
            return 0

        if new_lights and config[CONF_ALLOW_LIGHTIFY_NODES]:
            new_entities = []
            for addr, light in new_lights.items():
                if (
                    light.devicetype().name == "SENSOR"
                    and not config[CONF_ALLOW_LIGHTIFY_SENSORS]
                ) or (
                    light.devicetype().name == "SWITCH"
                    and not config[CONF_ALLOW_LIGHTIFY_SWITCHES]
                ):
                    continue

                if addr not in lights:
                    osram_light = OsramLightifyLight(
                        light, update_lights, lights_changed
                    )
                    lights[addr] = osram_light
                    new_entities.append(osram_light)
                else:
                    lights[addr].update_luminary(light)

            add_entities(new_entities)

        return lights_changed