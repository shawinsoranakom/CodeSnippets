def _validate_webhooks(
        self,
        user_input: dict[str, Any],
        errors: dict[str, str],
        description_placeholders: dict[str, str],
    ) -> None:
        # validate URL
        url: str | None = user_input.get(CONF_URL)
        if url is None:
            try:
                get_url(self.hass, require_ssl=True, allow_internal=False)
            except NoURLAvailableError:
                errors["base"] = "no_url_available"
                description_placeholders[ERROR_FIELD] = "URL"
                description_placeholders[ERROR_MESSAGE] = (
                    "URL is required since you have not configured an external URL in Home Assistant"
                )
                return
        elif (
            not url.startswith("https")
            and self._step_user_data[CONF_API_ENDPOINT] == DEFAULT_API_ENDPOINT
        ):
            errors["base"] = "invalid_url"
            description_placeholders[ERROR_FIELD] = "URL"
            description_placeholders[ERROR_MESSAGE] = "URL must start with https"
            return

        # validate trusted networks
        csv_trusted_networks: list[str] = []
        formatted_trusted_networks: str = (
            user_input[CONF_TRUSTED_NETWORKS].lstrip("[").rstrip("]")
        )
        for trusted_network in cv.ensure_list_csv(formatted_trusted_networks):
            formatted_trusted_network: str = trusted_network.strip("'")
            try:
                IPv4Network(formatted_trusted_network)
            except (AddressValueError, ValueError) as err:
                errors["base"] = "invalid_trusted_networks"
                description_placeholders[ERROR_FIELD] = "trusted networks"
                description_placeholders[ERROR_MESSAGE] = str(err)
                return
            else:
                csv_trusted_networks.append(formatted_trusted_network)
        user_input[CONF_TRUSTED_NETWORKS] = csv_trusted_networks

        return