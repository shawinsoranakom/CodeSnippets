async def async_step_usb(self, discovery_info: UsbServiceInfo) -> ConfigFlowResult:
        """Handle USB Discovery."""
        if not is_hassio(self.hass):
            return self.async_abort(reason="discovery_requires_supervisor")
        if any(
            flow
            for flow in self._async_in_progress()
            if flow["context"].get("source") != SOURCE_USB
        ):
            # Allow multiple USB discovery flows to be in progress.
            # Migration requires more than one USB stick to be connected,
            # which can cause more than one discovery flow to be in progress,
            # at least for a short time.
            return self.async_abort(reason="already_in_progress")
        if current_config_entries := self._async_current_entries(include_ignore=False):
            self._reconfigure_config_entry = next(
                (
                    entry
                    for entry in current_config_entries
                    if entry.data.get(CONF_USE_ADDON)
                ),
                None,
            )
            if not self._reconfigure_config_entry:
                return self.async_abort(
                    reason="addon_required",
                    description_placeholders={
                        "zwave_js_ui_migration": ZWAVE_JS_UI_MIGRATION_INSTRUCTIONS,
                    },
                )

        vid = discovery_info.vid
        pid = discovery_info.pid
        serial_number = discovery_info.serial_number
        manufacturer = discovery_info.manufacturer
        description = discovery_info.description
        # Zooz uses this vid/pid, but so do 2652 sticks
        if vid == "10C4" and pid == "EA60" and description and "2652" in description:
            return self.async_abort(reason="not_zwave_device")

        discovery_info.device = await self.hass.async_add_executor_job(
            usb.get_serial_by_id, discovery_info.device
        )

        addon_info = await self._async_get_addon_info()
        if (
            addon_info.state not in (AddonState.NOT_INSTALLED, AddonState.INSTALLING)
            and (addon_device := addon_info.options.get(CONF_ADDON_DEVICE)) is not None
            and await self.hass.async_add_executor_job(
                usb.get_serial_by_id, addon_device
            )
            == discovery_info.device
        ):
            return self.async_abort(reason="already_configured")

        await self.async_set_unique_id(
            f"{vid}:{pid}_{serial_number}_{manufacturer}_{description}"
        )
        # We don't need to check if the unique_id is already configured
        # since we will update the unique_id before finishing the flow.
        # The unique_id set above is just a temporary value to avoid
        # duplicate discovery flows.
        dev_path = discovery_info.device
        self.usb_path = dev_path
        if manufacturer == "Nabu Casa" and description == "ZWA-2 - Nabu Casa ZWA-2":
            title = "Home Assistant Connect ZWA-2"
        else:
            human_name = usb.human_readable_device_name(
                dev_path,
                serial_number,
                manufacturer,
                description,
                vid,
                pid,
            )
            title = human_name.split(" - ")[0].strip()
        self.context["title_placeholders"] = {CONF_NAME: title}

        self._adapter_discovered = True
        if current_config_entries:
            return await self.async_step_confirm_usb_migration()

        return await self.async_step_installation_type()