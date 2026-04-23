def async_add_device(_: EventType, device_id: str) -> None:
            """Add device or add it to ignored_devices set.

            If ignore_state_updates is True means device_refresh service is used.
            Device_refresh is expected to load new devices.
            """
            if (
                not initializing
                and not self.config.allow_new_devices
                and not self.ignore_state_updates
            ):
                self.ignored_devices.add((async_add_device, device_id))
                return

            if isinstance(deconz_device_interface, GroupHandler):
                self.deconz_groups.add((async_add_device, device_id))
                if not self.config.allow_deconz_groups:
                    return

            if isinstance(deconz_device_interface, SENSORS):
                device = deconz_device_interface[device_id]
                if device.type.startswith("CLIP") and not always_ignore_clip_sensors:
                    self.clip_sensors.add((async_add_device, device_id))
                    if not self.config.allow_clip_sensor:
                        return

            add_device_callback(EventType.ADDED, device_id)