def update_from_latest_data(self) -> None:
        """Update the sensor."""
        if not self.coordinator.last_update_success:
            return

        try:
            if self.entity_description.key in (
                TYPE_ALLERGY_TODAY,
                TYPE_ALLERGY_TOMORROW,
                TYPE_ASTHMA_TODAY,
                TYPE_ASTHMA_TOMORROW,
                TYPE_DISEASE_TODAY,
            ):
                data = self.coordinator.data.get("Location")
        except KeyError:
            return

        key = self.entity_description.key.split("_")[-1].title()

        try:
            period = next(p for p in data["periods"] if p["Type"] == key)  # type: ignore[index]
        except StopIteration:
            return

        data = cast(dict[str, Any], data)
        [rating] = [
            i.label for i in RATING_MAPPING if i.minimum <= period["Index"] <= i.maximum
        ]

        self._attr_extra_state_attributes.update(
            {
                ATTR_CITY: data["City"].title(),
                ATTR_RATING: rating,
                ATTR_STATE: data["State"],
                ATTR_ZIP_CODE: data["ZIP"],
            }
        )

        if self.entity_description.key in (TYPE_ALLERGY_TODAY, TYPE_ALLERGY_TOMORROW):
            for idx, attrs in enumerate(period["Triggers"]):
                index = idx + 1
                self._attr_extra_state_attributes.update(
                    {
                        f"{ATTR_ALLERGEN_GENUS}_{index}": attrs["Genus"],
                        f"{ATTR_ALLERGEN_NAME}_{index}": attrs["Name"],
                        f"{ATTR_ALLERGEN_TYPE}_{index}": attrs["PlantType"],
                    }
                )
        elif self.entity_description.key in (TYPE_ASTHMA_TODAY, TYPE_ASTHMA_TOMORROW):
            for idx, attrs in enumerate(period["Triggers"]):
                index = idx + 1
                self._attr_extra_state_attributes.update(
                    {
                        f"{ATTR_ALLERGEN_NAME}_{index}": attrs["Name"],
                        f"{ATTR_ALLERGEN_AMOUNT}_{index}": attrs["PPM"],
                    }
                )
        elif self.entity_description.key == TYPE_DISEASE_TODAY:
            for attrs in period["Triggers"]:
                self._attr_extra_state_attributes[f"{attrs['Name'].lower()}_index"] = (
                    attrs["Index"]
                )

        self._attr_native_value = period["Index"]