async def _configure_component(
        self, hass: HomeAssistant, controller_config: ControllerConfig
    ) -> ControllerData:
        """Configure the component with specific mock data."""
        component_config = {
            **(controller_config.config or {}),
            **(controller_config.options or {}),
        }

        if controller_config.legacy_entity_unique_id:
            component_config[CONF_LEGACY_UNIQUE_ID] = True

        controller: pv.VeraController = MagicMock()
        controller.base_url = component_config.get(CONF_CONTROLLER)
        controller.register = MagicMock()
        controller.start = MagicMock()
        controller.stop = MagicMock()
        controller.refresh_data = MagicMock()
        controller.temperature_units = "C"
        controller.serial_number = controller_config.serial_number
        controller.get_devices = MagicMock(return_value=controller_config.devices)
        controller.get_scenes = MagicMock(return_value=controller_config.scenes)

        for vera_obj in controller.get_devices() + controller.get_scenes():
            vera_obj.vera_controller = controller

        controller.get_devices.reset_mock()
        controller.get_scenes.reset_mock()

        if controller_config.setup_callback:
            controller_config.setup_callback(controller)

        self.vera_controller_class_mock.return_value = controller

        # Setup component through config flow.
        if controller_config.config_source == ConfigSource.CONFIG_FLOW:
            await hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": config_entries.SOURCE_USER},
                data=component_config,
            )
            await hass.async_block_till_done()

        # Setup component directly from config entry.
        if controller_config.config_source == ConfigSource.CONFIG_ENTRY:
            entry = MockConfigEntry(
                domain=DOMAIN,
                data=controller_config.config,
                options=controller_config.options,
                unique_id="12345",
            )
            entry.add_to_hass(hass)

            await hass.config_entries.async_setup(entry.entry_id)
            await hass.async_block_till_done()

        update_callback = (
            controller.register.call_args_list[0][0][1]
            if controller.register.call_args_list
            else None
        )

        return ControllerData(controller=controller, update_callback=update_callback)