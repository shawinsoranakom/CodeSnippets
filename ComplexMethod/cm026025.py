async def async_step_plant(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle adding a "plant" to Home Assistant."""
        if self.auth_type == AUTH_API_TOKEN:
            # Using V1 API with token
            if not self.plants:
                return self.async_abort(reason=ABORT_NO_PLANTS)

            # Create dictionary of plant_id -> name
            plant_dict = {
                str(plant["plant_id"]): plant.get("name", "Unknown Plant")
                for plant in self.plants
            }

            if user_input is None and len(plant_dict) > 1:
                data_schema = vol.Schema(
                    {vol.Required(CONF_PLANT_ID): vol.In(plant_dict)}
                )
                return self.async_show_form(step_id="plant", data_schema=data_schema)

            if user_input is None:
                # Single plant => mark it as selected
                user_input = {CONF_PLANT_ID: list(plant_dict.keys())[0]}

            user_input[CONF_NAME] = plant_dict[user_input[CONF_PLANT_ID]]

        else:
            # Traditional API
            try:
                plant_info = await self.hass.async_add_executor_job(
                    self.api.plant_list, self.user_id
                )
            except requests.exceptions.RequestException as ex:
                _LOGGER.error("Network error during Growatt API plant list: %s", ex)
                return self.async_abort(reason=ERROR_CANNOT_CONNECT)

            # Access plant_info["data"] - validate response structure
            if not isinstance(plant_info, dict) or "data" not in plant_info:
                _LOGGER.error(
                    "Invalid response format during plant list: missing 'data' key"
                )
                return self.async_abort(reason=ERROR_CANNOT_CONNECT)

            plant_data = plant_info["data"]

            if not plant_data:
                return self.async_abort(reason=ABORT_NO_PLANTS)

            plants = {plant["plantId"]: plant["plantName"] for plant in plant_data}

            if user_input is None and len(plant_data) > 1:
                data_schema = vol.Schema({vol.Required(CONF_PLANT_ID): vol.In(plants)})
                return self.async_show_form(step_id="plant", data_schema=data_schema)

            if user_input is None:
                # single plant => mark it as selected
                user_input = {CONF_PLANT_ID: plant_data[0]["plantId"]}

            user_input[CONF_NAME] = plants[user_input[CONF_PLANT_ID]]

        await self.async_set_unique_id(user_input[CONF_PLANT_ID])
        self._abort_if_unique_id_configured()
        self.data.update(user_input)
        return self.async_create_entry(title=self.data[CONF_NAME], data=self.data)