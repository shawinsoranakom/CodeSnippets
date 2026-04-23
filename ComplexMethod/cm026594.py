async def async_step_init(
        self, user_input: dict[str, str]
    ) -> data_entry_flow.FlowResult:
        """Handle the steps of a fix flow."""
        if user_input.get(CONF_CHAT_MODEL):
            self._async_update_current_subentry(user_input)

        target = await self._async_next_target()
        if target is None:
            return self.async_create_entry(data={})

        entry, subentry, model = target
        if self._model_list_cache is None:
            self._model_list_cache = {}
        if entry.entry_id in self._model_list_cache:
            model_list = self._model_list_cache[entry.entry_id]
        else:
            client = entry.runtime_data.client
            model_list = [
                model_option
                for model_option in await self.get_model_list(client)
                if model_option["value"] not in DEPRECATED_MODELS
            ]
            self._model_list_cache[entry.entry_id] = model_list

        if "opus" in model:
            family = "claude-opus"
        elif "sonnet" in model:
            family = "claude-sonnet"
        else:
            family = "claude-haiku"

        suggested_model = next(
            (
                model_option["value"]
                for model_option in sorted(
                    (m for m in model_list if family in m["value"]),
                    key=lambda x: x["value"],
                    reverse=True,
                )
            ),
            vol.UNDEFINED,
        )

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_CHAT_MODEL,
                    default=suggested_model,
                ): SelectSelector(
                    SelectSelectorConfig(options=model_list, custom_value=True)
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            description_placeholders={
                "entry_name": entry.title,
                "model": model,
                "subentry_name": subentry.title,
                "subentry_type": self._format_subentry_type(subentry.subentry_type),
                "retirement_date": DEPRECATED_MODELS[model],
            },
        )