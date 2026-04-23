async def step_common(
        self,
        user_input: dict[str, Any] | None,
        obs_type: ObservationTypes,
        reconfiguring: bool = False,
    ) -> SubentryFlowResult:
        """Use common logic within the named steps."""

        errors: dict[str, str] = {}

        other_subentries = None
        if obs_type == str(ObservationTypes.NUMERIC_STATE):
            other_subentries = [
                dict(se.data) for se in self._get_entry().subentries.values()
            ]
        # If we are reconfiguring a subentry we don't want to compare with self
        if reconfiguring:
            sub_entry = self._get_reconfigure_subentry()
            if other_subentries is not None:
                other_subentries.remove(dict(sub_entry.data))

        if user_input is not None:
            try:
                user_input = _validate_observation_subentry(
                    obs_type,
                    user_input,
                    other_subentries=other_subentries,
                )
                if reconfiguring:
                    return self.async_update_and_abort(
                        self._get_entry(),
                        sub_entry,
                        title=user_input.get(CONF_NAME, sub_entry.data[CONF_NAME]),
                        data_updates=user_input,
                    )
                return self.async_create_entry(
                    title=user_input.get(CONF_NAME),
                    data=user_input,
                )
            except SchemaFlowError as err:
                errors["base"] = str(err)

        return self.async_show_form(
            step_id="reconfigure" if reconfiguring else str(obs_type),
            data_schema=self.add_suggested_values_to_schema(
                data_schema=_select_observation_schema(obs_type),
                suggested_values=_get_observation_values_for_editing(sub_entry)
                if reconfiguring
                else None,
            ),
            errors=errors,
            description_placeholders={
                "parent_sensor_name": self._get_entry().title,
                "device_class_on": translation.async_translate_state(
                    self.hass,
                    "on",
                    BINARY_SENSOR_DOMAIN,
                    platform=None,
                    translation_key=None,
                    device_class=self._get_entry().options.get(CONF_DEVICE_CLASS, None),
                ),
                "device_class_off": translation.async_translate_state(
                    self.hass,
                    "off",
                    BINARY_SENSOR_DOMAIN,
                    platform=None,
                    translation_key=None,
                    device_class=self._get_entry().options.get(CONF_DEVICE_CLASS, None),
                ),
            },
        )