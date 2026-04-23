async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle a user initiated set up flow to create a webhook."""
        if (
            not self._allow_multiple
            and self._async_current_entries()
            and self.source != config_entries.SOURCE_RECONFIGURE
        ):
            return self.async_abort(reason="single_instance_allowed")

        if user_input is None:
            return self.async_show_form(
                step_id="reconfigure"
                if self.source == config_entries.SOURCE_RECONFIGURE
                else "user"
            )

        # Local import to be sure cloud is loaded and setup
        from homeassistant.components.cloud import (  # noqa: PLC0415
            async_active_subscription,
            async_create_cloudhook,
            async_is_connected,
        )

        # Local import to be sure webhook is loaded and setup
        from homeassistant.components.webhook import (  # noqa: PLC0415
            async_generate_id,
            async_generate_url,
        )

        if self.source == config_entries.SOURCE_RECONFIGURE:
            entry = self._get_reconfigure_entry()
            webhook_id = entry.data["webhook_id"]
        else:
            webhook_id = async_generate_id()

        if "cloud" in self.hass.config.components and async_active_subscription(
            self.hass
        ):
            if not async_is_connected(self.hass):
                return self.async_abort(reason="cloud_not_connected")

            webhook_url = await async_create_cloudhook(self.hass, webhook_id)
            cloudhook = True
        else:
            webhook_url = async_generate_url(self.hass, webhook_id)
            cloudhook = False

        self._description_placeholder["webhook_url"] = webhook_url

        if self.source == config_entries.SOURCE_RECONFIGURE:
            if self.hass.config_entries.async_update_entry(
                entry=entry,
                data={**entry.data, "webhook_id": webhook_id, "cloudhook": cloudhook},
            ):
                self.hass.config_entries.async_schedule_reload(entry.entry_id)
            return self.async_abort(
                reason="reconfigure_successful",
                description_placeholders=self._description_placeholder,
            )

        return self.async_create_entry(
            title=self._title,
            data={"webhook_id": webhook_id, "cloudhook": cloudhook},
            description_placeholders=self._description_placeholder,
        )