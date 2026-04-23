async def async_step_reconfigure_ups(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle selecting the NUT device alias."""

        errors: dict[str, str] = {}
        placeholders: dict[str, str] = {}
        reconfigure_entry = self._get_reconfigure_entry()
        nut_config = self.nut_config

        if user_input is not None:
            self.nut_config.update(user_input)

            if not _check_host_port_alias_match(
                reconfigure_entry.data,
                nut_config,
            ) and (self._host_port_alias_already_configured(nut_config)):
                return self.async_abort(reason="already_configured")

            info, errors, placeholders = await self._async_validate_or_error(nut_config)
            if not errors:
                if unique_id := _unique_id_from_status(info["available_resources"]):
                    await self.async_set_unique_id(unique_id)
                    self._abort_if_unique_id_mismatch(reason="unique_id_mismatch")

                if nut_config[CONF_PASSWORD] == PASSWORD_NOT_CHANGED:
                    nut_config.pop(CONF_PASSWORD)

                new_title = _format_host_port_alias(nut_config)
                return self.async_update_reload_and_abort(
                    self._get_reconfigure_entry(),
                    unique_id=unique_id,
                    title=new_title,
                    data_updates=nut_config,
                )

        return self.async_show_form(
            step_id="reconfigure_ups",
            data_schema=_ups_schema(self.ups_list or {}),
            errors=errors,
            description_placeholders=placeholders,
        )