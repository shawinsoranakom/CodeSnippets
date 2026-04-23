async def async_update_data(self) -> None:
        """Update the data from the SolarEdge Monitoring API."""
        try:
            data = await self.api.get_current_power_flow(self.site_id)
            power_flow = data["siteCurrentPowerFlow"]
        except KeyError as ex:
            raise UpdateFailed("Missing power flow data, skipping update") from ex

        power_from = []
        power_to = []

        if "connections" not in power_flow:
            LOGGER.debug(
                "Missing connections in power flow data. Assuming site does not"
                " have any"
            )
            return

        for connection in power_flow["connections"]:
            power_from.append(connection["from"].lower())
            power_to.append(connection["to"].lower())

        self.data = {}
        self.attributes = {}
        self.unit = power_flow["unit"]

        for key, value in power_flow.items():
            if key in ["LOAD", "PV", "GRID", "STORAGE"]:
                self.data[key] = value.get("currentPower")
                self.attributes[key] = {"status": value["status"]}

            if key == "GRID":
                export = key.lower() in power_to
                if self.data[key]:
                    self.data[key] *= -1 if export else 1
                self.attributes[key]["flow"] = "export" if export else "import"

            if key == "STORAGE":
                charge = key.lower() in power_to
                if self.data[key]:
                    self.data[key] *= -1 if charge else 1
                self.attributes[key]["flow"] = "charge" if charge else "discharge"
                self.attributes[key]["soc"] = value["chargeLevel"]

        LOGGER.debug("Updated SolarEdge power flow: %s, %s", self.data, self.attributes)