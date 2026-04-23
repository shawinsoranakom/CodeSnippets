async def _async_update(self) -> None:
        """Get the latest data and updates the state."""
        await self.data.async_update()
        value = self.data.value

        variables = self._template_variables_with_value(self.data.value)
        if not self._render_availability_template(variables):
            self.async_write_ha_state()
            return

        if self._json_attributes:
            self._attr_extra_state_attributes = {}
            if value:
                try:
                    json_dict = json.loads(value)
                    if self._json_attributes_path is not None:
                        json_dict = jsonpath(json_dict, self._json_attributes_path)
                    # jsonpath will always store the result in json_dict[0]
                    # so the next line happens to work exactly as needed to
                    # find the result
                    if isinstance(json_dict, list):
                        json_dict = json_dict[0]
                    if isinstance(json_dict, Mapping):
                        self._attr_extra_state_attributes = {
                            k: json_dict[k]
                            for k in self._json_attributes
                            if k in json_dict
                        }
                    else:
                        LOGGER.warning("JSON result was not a dictionary")
                except ValueError:
                    LOGGER.warning("Unable to parse output as JSON: %s", value)
            else:
                LOGGER.warning("Empty reply found when expecting JSON data")

            if self._value_template is None:
                self._attr_native_value = None
                self._process_manual_data(variables)
                self.async_write_ha_state()
                return

        self._attr_native_value = None
        if self._value_template is not None and value is not None:
            value = self._value_template.async_render_as_value_template(
                self.entity_id, variables, None
            )

        self._set_native_value_with_possible_timestamp(value)
        self._process_manual_data(variables)
        self.async_write_ha_state()