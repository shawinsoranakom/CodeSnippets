async def async_step_multiple_cameras(
        self, user_input: dict[str, str] | None = None
    ) -> ConfigFlowResult:
        """Handle when multiple cameras."""

        if user_input:
            errors, cameras = await self.validate_input(
                self.api_key, user_input[CONF_ID]
            )

            if not errors and cameras:
                if self.source == SOURCE_RECONFIGURE:
                    return self.async_update_reload_and_abort(
                        self._get_reconfigure_entry(),
                        unique_id=f"{DOMAIN}-{cameras[0].camera_id}",
                        title=cameras[0].camera_name or "Trafikverket Camera",
                        data={
                            CONF_API_KEY: self.api_key,
                            CONF_ID: cameras[0].camera_id,
                        },
                    )
                await self.async_set_unique_id(f"{DOMAIN}-{cameras[0].camera_id}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=cameras[0].camera_name or "Trafikverket Camera",
                    data={CONF_API_KEY: self.api_key, CONF_ID: cameras[0].camera_id},
                )

        camera_choices = [
            SelectOptionDict(
                value=f"{camera_info.camera_id}",
                label=f"{camera_info.camera_id} - {camera_info.camera_name} - {camera_info.location}",
            )
            for camera_info in self.cameras
        ]

        return self.async_show_form(
            step_id="multiple_cameras",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ID): SelectSelector(
                        SelectSelectorConfig(
                            options=camera_choices, mode=SelectSelectorMode.LIST
                        )
                    ),
                }
            ),
        )