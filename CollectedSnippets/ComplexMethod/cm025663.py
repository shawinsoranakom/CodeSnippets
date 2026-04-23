async def async_update_data(self) -> None:
        """Update the data from the SolarEdge Monitoring API."""
        try:
            now = datetime.now()
            today = date.today()
            midnight = datetime.combine(today, datetime.min.time())
            data = await self.api.get_energy_details(
                self.site_id,
                midnight,
                now,
                time_unit="DAY",
            )
            energy_details = data["energyDetails"]
        except KeyError as ex:
            raise UpdateFailed("Missing power flow data, skipping update") from ex

        if "meters" not in energy_details:
            LOGGER.debug(
                "Missing meters in energy details data. Assuming site does not have any"
            )
            return

        self.data = {}
        self.attributes = {}
        self.unit = energy_details["unit"]

        for meter in energy_details["meters"]:
            if "type" not in meter or "values" not in meter:
                continue
            if meter["type"] not in [
                "Production",
                "SelfConsumption",
                "FeedIn",
                "Purchased",
                "Consumption",
            ]:
                continue
            if len(meter["values"][0]) == 2:
                self.data[meter["type"]] = meter["values"][0]["value"]
                self.attributes[meter["type"]] = {"date": meter["values"][0]["date"]}

        LOGGER.debug(
            "Updated SolarEdge energy details: %s, %s", self.data, self.attributes
        )