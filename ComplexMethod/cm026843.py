def _update_fritz_devices(self) -> FritzboxCoordinatorData:
        """Update all fritzbox device data."""
        self.fritz.update_devices(ignore_removed=False)
        if self.has_templates:
            self.fritz.update_templates(ignore_removed=False)
        if self.has_triggers:
            self.fritz.update_triggers(ignore_removed=False)

        devices = self.fritz.get_devices()
        device_data = {}
        supported_color_properties = self.data.supported_color_properties
        for device in devices:
            # assume device as unavailable, see #55799
            if (
                device.has_powermeter
                and device.present
                and isinstance(device.voltage, int)
                and device.voltage <= 0
                and isinstance(device.power, int)
                and device.power <= 0
                and device.energy <= 0
            ):
                LOGGER.debug("Assume device %s as unavailable", device.name)
                device.present = False

            device_data[device.ain] = device

            # pre-load supported colors and color temps for new devices
            if device.has_color and device.ain not in supported_color_properties:
                supported_color_properties[device.ain] = (
                    device.get_colors(),
                    device.get_color_temps(),
                )

        template_data = {}
        if self.has_templates:
            templates = self.fritz.get_templates()
            for template in templates:
                template_data[template.ain] = template

        trigger_data = {}
        if self.has_triggers:
            triggers = self.fritz.get_triggers()
            for trigger in triggers:
                trigger_data[trigger.ain] = trigger

        self.new_devices = device_data.keys() - self.data.devices.keys()
        self.new_templates = template_data.keys() - self.data.templates.keys()
        self.new_triggers = trigger_data.keys() - self.data.triggers.keys()

        return FritzboxCoordinatorData(
            devices=device_data,
            templates=template_data,
            triggers=trigger_data,
            supported_color_properties=supported_color_properties,
        )