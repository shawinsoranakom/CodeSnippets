async def async_step_model(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Handle the model selection step."""
        errors: dict[str, str] = {}

        if not self.models:
            try:
                self.models = await self._async_get_models(
                    self_only=self.config_data.get(CONF_SELF_ONLY, False),
                    language=self.config_data.get(CONF_LANGUAGE),
                    title=self.config_data.get(CONF_TITLE),
                    sort_by=self.config_data.get(CONF_SORT_BY, "task_count"),
                )
            except CannotGetModelsError:
                return self.async_abort(reason="cannot_connect")

            if not self.models:
                return self.async_abort(reason="no_models_found")

            if CONF_VOICE_ID not in self.config_data and self.models:
                self.config_data[CONF_VOICE_ID] = self.models[0]["value"]

        if user_input is not None:
            if (
                (voice_id := user_input.get(CONF_VOICE_ID))
                and (backend := user_input.get(CONF_BACKEND))
                and (name := user_input.get(CONF_NAME))
            ):
                self.config_data.update(user_input)
                unique_id = f"{voice_id}-{backend}"

                if self.source == SOURCE_USER:
                    return self.async_create_entry(
                        title=name,
                        data=self.config_data,
                        unique_id=unique_id,
                    )

                return self.async_update_and_abort(
                    self._get_entry(),
                    self._get_reconfigure_subentry(),
                    data=self.config_data,
                    unique_id=unique_id,
                )

        return self.async_show_form(
            step_id="model",
            data_schema=get_model_selection_schema(self.config_data, self.models),
            errors=errors,
        )