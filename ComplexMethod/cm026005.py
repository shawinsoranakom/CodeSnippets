async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Manage AI task configuration."""
        if self._get_entry().state != ConfigEntryState.LOADED:
            return self.async_abort(reason="entry_not_loaded")

        if user_input is not None:
            if self._is_new:
                return self.async_create_entry(
                    title=self.models[user_input[CONF_MODEL]].name, data=user_input
                )
            return self.async_update_and_abort(
                self._get_entry(),
                self._get_reconfigure_subentry(),
                data=user_input,
            )

        try:
            await self._get_models()
        except OpenRouterError:
            return self.async_abort(reason="cannot_connect")
        except Exception:
            _LOGGER.exception("Unexpected exception")
            return self.async_abort(reason="unknown")

        options = [
            SelectOptionDict(value=model.id, label=model.name)
            for model in self.models.values()
            if SupportedParameter.STRUCTURED_OUTPUTS in model.supported_parameters
        ]

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_MODEL, default=self.options.get(CONF_MODEL)
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=options, mode=SelectSelectorMode.DROPDOWN, sort=True
                        ),
                    ),
                }
            ),
        )