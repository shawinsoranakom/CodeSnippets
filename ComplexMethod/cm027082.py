async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle the bluetooth discovery step."""
        _LOGGER.debug("Discovered bluetooth device: %s", discovery_info.as_dict())
        await self.async_set_unique_id(format_unique_id(discovery_info.address))
        self._abort_if_unique_id_configured()
        parsed = parse_advertisement_data(
            discovery_info.device, discovery_info.advertisement
        )
        if not parsed or parsed.data.get("modelName") not in SUPPORTED_MODEL_TYPES:
            return self.async_abort(reason="not_supported")
        model_name = parsed.data.get("modelName")
        if (
            not discovery_info.connectable
            and model_name in CONNECTABLE_SUPPORTED_MODEL_TYPES
            and model_name not in NON_CONNECTABLE_SUPPORTED_MODEL_TYPES
        ):
            # Source is not connectable but the model is connectable only
            return self.async_abort(reason="not_supported")
        self._discovered_adv = parsed
        data = parsed.data
        self.context["title_placeholders"] = {
            "name": data["modelFriendlyName"],
            "address": short_address(discovery_info.address),
        }
        if model_name in ENCRYPTED_MODELS:
            return await self.async_step_encrypted_choose_method()
        if self._discovered_adv.data["isEncrypted"]:
            return await self.async_step_password()
        return await self.async_step_confirm()