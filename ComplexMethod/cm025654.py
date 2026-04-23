async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage Crownstone options."""
        self.cloud = self.config_entry.runtime_data.cloud

        spheres = {sphere.name: sphere.cloud_id for sphere in self.cloud.cloud_data}
        usb_path = self.config_entry.options.get(CONF_USB_PATH)
        usb_sphere = self.config_entry.options.get(CONF_USB_SPHERE)

        options_schema = vol.Schema(
            {vol.Optional(CONF_USE_USB_OPTION, default=usb_path is not None): bool}
        )
        if usb_path is not None and len(spheres) > 1:
            options_schema = options_schema.extend(
                {
                    vol.Optional(
                        CONF_USB_SPHERE_OPTION,
                        default=self.cloud.cloud_data.data[usb_sphere].name,
                    ): vol.In(spheres.keys())
                }
            )

        if user_input is not None:
            if user_input[CONF_USE_USB_OPTION] and usb_path is None:
                return await self.async_step_usb_config()
            if not user_input[CONF_USE_USB_OPTION] and usb_path is not None:
                self.options[CONF_USB_PATH] = None
                self.options[CONF_USB_SPHERE] = None
            elif (
                CONF_USB_SPHERE_OPTION in user_input
                and spheres[user_input[CONF_USB_SPHERE_OPTION]] != usb_sphere
            ):
                sphere_id = spheres[user_input[CONF_USB_SPHERE_OPTION]]
                self.options[CONF_USB_SPHERE] = sphere_id

            return self.async_create_new_entry()

        return self.async_show_form(step_id="init", data_schema=options_schema)