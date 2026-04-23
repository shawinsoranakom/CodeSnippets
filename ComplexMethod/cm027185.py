def daily_forecast(self) -> list[Forecast] | None:
        """Return the daily forecast in native units."""
        data: list[Forecast] = self.coordinator.data.daily_forecast

        # The data in daily_forecast might contain nighttime forecast.
        # The following handle the lowest temperature attribute to be displayed correctly.
        if (
            len(data) > 1
            and not data[0].get("is_daytime")
            and data[1].get("native_templow") is None
        ):
            data[1]["native_templow"] = data[0].get("native_templow")
            if (
                data[1]["native_templow"] is not None
                and data[1]["native_temperature"] is not None
                and data[1]["native_templow"] > data[1]["native_temperature"]
            ):
                (data[1]["native_templow"], data[1]["native_temperature"]) = (
                    data[1]["native_temperature"],
                    data[1]["native_templow"],
                )

        if len(data) > 0 and not data[0].get("is_daytime"):
            return data

        if (
            len(data) > 1
            and data[0].get("native_templow") is None
            and not data[1].get("is_daytime")
        ):
            data[0]["native_templow"] = data[1].get("native_templow")
            if (
                data[0]["native_templow"] is not None
                and data[0]["native_temperature"] is not None
                and data[0]["native_templow"] > data[0]["native_temperature"]
            ):
                (data[0]["native_templow"], data[0]["native_temperature"]) = (
                    data[0]["native_temperature"],
                    data[0]["native_templow"],
                )

        return [f for f in data if f.get("is_daytime")]