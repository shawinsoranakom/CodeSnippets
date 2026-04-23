def icon(self) -> str:
        """Return an icon."""

        if self._service_name == "Call Direction":
            if self._attr_native_value == "No Active Calls":
                return "mdi:phone-off"
            if self._attr_native_value == "Inbound Call":
                return "mdi:phone-incoming"
            return "mdi:phone-outgoing"
        if "Caller Info" in self._service_name:
            return "mdi:phone-log"
        if "Port" in self._service_name:
            if self._attr_native_value == "Ringing":
                return "mdi:phone-ring"
            if self._attr_native_value == "Off Hook":
                return "mdi:phone-in-talk"
            return "mdi:phone-hangup"
        if "Service Status" in self._service_name:
            if "OBiTALK Service Status" in self._service_name:
                return "mdi:phone-check"
            if self._attr_native_value == "0":
                return "mdi:phone-hangup"
            return "mdi:phone-in-talk"
        if "Reboot Required" in self._service_name:
            if self._attr_native_value == "false":
                return "mdi:restart-off"
            return "mdi:restart-alert"
        return "mdi:phone"