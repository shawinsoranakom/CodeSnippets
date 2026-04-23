def _handle(self, hass, data):
        for i in data["data"]["observations"]:
            data["data"]["secret"] = "hidden"

            lat = i["location"]["lat"]
            lng = i["location"]["lng"]
            try:
                accuracy = int(float(i["location"]["unc"]))
            except ValueError:
                accuracy = 0

            mac = i["clientMac"]
            _LOGGER.debug("clientMac: %s", mac)

            if lat == "NaN" or lng == "NaN":
                _LOGGER.debug("No coordinates received, skipping location for: %s", mac)
                gps_location = None
                accuracy = None
            else:
                gps_location = (lat, lng)

            attrs = {}
            if i.get("os", False):
                attrs["os"] = i["os"]
            if i.get("manufacturer", False):
                attrs["manufacturer"] = i["manufacturer"]
            if i.get("ipv4", False):
                attrs["ipv4"] = i["ipv4"]
            if i.get("ipv6", False):
                attrs["ipv6"] = i["ipv6"]
            if i.get("seenTime", False):
                attrs["seenTime"] = i["seenTime"]
            if i.get("ssid", False):
                attrs["ssid"] = i["ssid"]
            hass.async_create_task(
                self.async_see(
                    gps=gps_location,
                    mac=mac,
                    source_type=SourceType.ROUTER,
                    gps_accuracy=accuracy,
                    attributes=attrs,
                )
            )