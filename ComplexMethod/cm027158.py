async def async_step_webhooks(
        self, user_input: dict[str, Any] | None
    ) -> ConfigFlowResult:
        """Dialog to setup webhooks."""
        system = self._data["system"]

        errors: dict[str, str] | None = None
        if user_input is not None:
            errors = {}
            for key, webhook_name in user_input.items():
                if key == CONF_URL:
                    continue
                if not re.match(VALID_NAME_PATTERN, webhook_name):
                    errors.update({key: "invalid_name"})
            try:
                cv.url(user_input[CONF_URL])
            except vol.Invalid:
                errors[CONF_URL] = "invalid_url"
            if set(user_input) == {CONF_URL}:
                errors["base"] = "no_webhooks_provided"

            if not errors:
                webhook_data = [
                    {
                        "auth": secrets.token_hex(32),
                        "name": webhook_name,
                        "webhook_id": webhook_generate_id(),
                    }
                    for key, webhook_name in user_input.items()
                    if key != CONF_URL
                ]
                for webhook in webhook_data:
                    wh_def: ekey_bionyxpy.WebhookData = {
                        "integrationName": "Home Assistant",
                        "functionName": webhook["name"],
                        "locationName": "Home Assistant",
                        "definition": {
                            "url": user_input[CONF_URL]
                            + webhook_generate_path(webhook["webhook_id"]),
                            "authentication": {"apiAuthenticationType": "None"},
                            "securityLevel": "AllowHttp",
                            "method": "Post",
                            "body": {
                                "contentType": "application/json",
                                "content": json.dumps({"auth": webhook["auth"]}),
                            },
                        },
                    }
                    webhook["ekey_id"] = (await system.add_webhook(wh_def)).webhook_id
                return self.async_create_entry(
                    title=self._data["system"].system_name,
                    data={"webhooks": webhook_data},
                )

        data_schema: dict[Any, Any] = {
            vol.Optional(f"webhook{i + 1}"): vol.All(str, vol.Length(max=50))
            for i in range(self._data["system"].function_webhook_quotas["free"])
        }
        data_schema[vol.Required(CONF_URL)] = str
        return self.async_show_form(
            step_id="webhooks",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(data_schema),
                {
                    CONF_URL: get_url(
                        self.hass,
                        allow_ip=True,
                        prefer_external=False,
                    )
                }
                | (user_input or {}),
            ),
            errors=errors,
            description_placeholders={
                "webhooks_available": str(
                    self._data["system"].function_webhook_quotas["free"]
                ),
                "ekeybionyx": INTEGRATION_NAME,
            },
        )