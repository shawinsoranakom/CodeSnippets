async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Yale."""

        updates = await self.hass.async_add_executor_job(self.get_updates)

        door_windows = []
        temp_sensors = []

        for device in updates["cycle"]["device_status"]:
            state = device["status1"]
            if device["type"] == "device_type.door_contact":
                device["_battery"] = False
                if "device_status.low_battery" in state:
                    device["_battery"] = True
                if "device_status.dc_close" in state:
                    device["_state"] = "closed"
                    door_windows.append(device)
                    continue
                if "device_status.dc_open" in state:
                    device["_state"] = "open"
                    door_windows.append(device)
                    continue
                device["_state"] = "unavailable"
                door_windows.append(device)
                continue
            if device["type"] == "device_type.temperature_sensor":
                temp_sensors.append(device)

        _sensor_map = {
            contact["address"]: contact["_state"] for contact in door_windows
        }
        _sensor_battery_map = {
            f"{contact['address']}-battery": contact["_battery"]
            for contact in door_windows
        }
        _temp_map = {temp["address"]: temp["status_temp"] for temp in temp_sensors}

        return {
            "alarm": updates["arm_status"],
            "door_windows": door_windows,
            "temp_sensors": temp_sensors,
            "status": updates["status"],
            "online": updates["online"],
            "sensor_map": _sensor_map,
            "sensor_battery_map": _sensor_battery_map,
            "temp_map": _temp_map,
            "panel_info": updates["panel_info"],
        }