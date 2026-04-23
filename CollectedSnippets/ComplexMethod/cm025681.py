def update_from_latest_data(self) -> None:
        """Update the sensor."""
        if not self.available:
            return

        data = self.coordinator.data.get("Location", {})

        if not data.get("periods"):
            return

        indices = [p["Index"] for p in data["periods"]]
        average = round(mean(indices), 1)
        [rating] = [
            i.label for i in RATING_MAPPING if i.minimum <= average <= i.maximum
        ]

        self._attr_native_value = average
        self._attr_extra_state_attributes.update(
            {
                ATTR_CITY: data["City"].title(),
                ATTR_RATING: rating,
                ATTR_STATE: data["State"],
                ATTR_TREND: calculate_trend(indices),
                ATTR_ZIP_CODE: data["ZIP"],
            }
        )

        if self.entity_description.key == TYPE_ALLERGY_FORECAST:
            outlook_coordinator = self._entry.runtime_data[TYPE_ALLERGY_OUTLOOK]

            if not outlook_coordinator.last_update_success:
                return

            self._attr_extra_state_attributes[ATTR_OUTLOOK] = (
                outlook_coordinator.data.get("Outlook")
            )
            self._attr_extra_state_attributes[ATTR_SEASON] = (
                outlook_coordinator.data.get("Season")
            )