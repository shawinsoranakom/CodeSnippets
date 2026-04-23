async def handle_subscription_data(self, data: SubscriptionData) -> None:
        """Handle subscription data."""
        self.logger.debug("Received subscription data: %s", data)
        self._should_log_subscription_error = True
        update_devices = set()
        for device in data.get("devices") or []:
            if (device_id := device["id"]) not in self.data:
                self.logger.debug("Device %s not found in data", device_id)
                continue

            if (
                attr
                := self._return_custom_attributes_if_not_filtered_by_accuracy_configuration(
                    device, self.data[device_id]["position"]
                )
            ) is None:
                continue

            self.data[device_id]["device"] = device
            self.data[device_id]["attributes"] = attr
            update_devices.add(device_id)

        for position in data.get("positions") or []:
            if (device_id := position["deviceId"]) not in self.data:
                self.logger.debug(
                    "Device %s for position %s not found in data",
                    device_id,
                    position["id"],
                )
                continue

            if (
                attr
                := self._return_custom_attributes_if_not_filtered_by_accuracy_configuration(
                    self.data[device_id]["device"], position
                )
            ) is None:
                self.logger.debug(
                    "Skipping position update %s for %s due to accuracy filter",
                    position["id"],
                    device_id,
                )
                continue

            self.data[device_id]["position"] = position
            self.data[device_id]["attributes"] = attr
            self.data[device_id]["geofence"] = get_first_geofence(
                self._geofences,
                get_geofence_ids(self.data[device_id]["device"], position),
            )
            update_devices.add(device_id)

        for device_id in update_devices:
            async_dispatcher_send(self.hass, f"{DOMAIN}_{device_id}")