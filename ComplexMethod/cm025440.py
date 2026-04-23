async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> ConfigFlowResult:
        """Handle zeroconf discovery."""
        _LOGGER.debug("Discovered NRGkick device: %s", discovery_info)

        # Extract device information from mDNS metadata.
        serial = discovery_info.properties.get("serial_number")
        device_name = discovery_info.properties.get("device_name")
        model_type = discovery_info.properties.get("model_type")
        json_api_enabled = discovery_info.properties.get("json_api_enabled", "0")

        if not serial:
            _LOGGER.debug("NRGkick device discovered without serial number")
            return self.async_abort(reason="no_serial_number")

        # Set unique ID to prevent duplicate entries.
        await self.async_set_unique_id(serial)
        # Update the host if the device is already configured (IP might have changed).
        self._abort_if_unique_id_configured(updates={CONF_HOST: discovery_info.host})

        # Store discovery info for the confirmation step.
        self._discovered_host = discovery_info.host
        # Fallback: device_name -> model_type -> "NRGkick".
        discovered_name = device_name or model_type or "NRGkick"
        self._discovered_name = discovered_name
        self.context["title_placeholders"] = {"name": discovered_name}

        # If JSON API is disabled, guide the user through enabling it.
        if json_api_enabled != "1":
            _LOGGER.debug("NRGkick device %s does not have JSON API enabled", serial)
            return await self.async_step_zeroconf_enable_json_api()

        try:
            await validate_input(self.hass, self._discovered_host)
        except NRGkickApiClientAuthenticationError:
            self._pending_host = self._discovered_host
            return await self.async_step_user_auth()
        except NRGkickApiClientApiDisabledError:
            # mDNS metadata may be stale; fall back to the enable guidance.
            return await self.async_step_zeroconf_enable_json_api()
        except (
            NRGkickApiClientCommunicationError,
            NRGkickApiClientInvalidResponseError,
        ):
            return self.async_abort(reason="cannot_connect")
        except NRGkickApiClientError:
            _LOGGER.exception("Unexpected error")
            return self.async_abort(reason="unknown")

        # Proceed to confirmation step (no auth required upfront).
        return await self.async_step_zeroconf_confirm()