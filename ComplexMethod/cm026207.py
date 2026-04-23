async def async_step_device_tracker(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the device tracker options."""
        if user_input is not None:
            self.options.update(user_input)
            return await self.async_step_client_control()

        ssids = (
            {wlan.name for wlan in self.hub.api.wlans.values()}
            | {
                f"{wlan.name}{wlan.name_combine_suffix}"
                for wlan in self.hub.api.wlans.values()
                if not wlan.name_combine_enabled
                and wlan.name_combine_suffix is not None
            }
            | {
                wlan["name"]
                for ap in self.hub.api.devices.values()
                for wlan in ap.wlan_overrides
                if "name" in wlan
            }
        )
        ssid_filter = {ssid: ssid for ssid in sorted(ssids)}

        selected_ssids_to_filter = [
            ssid for ssid in self.hub.config.option_ssid_filter if ssid in ssid_filter
        ]

        return self.async_show_form(
            step_id="device_tracker",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_TRACK_CLIENTS,
                        default=self.hub.config.option_track_clients,
                    ): bool,
                    vol.Optional(
                        CONF_TRACK_WIRED_CLIENTS,
                        default=self.hub.config.option_track_wired_clients,
                    ): bool,
                    vol.Optional(
                        CONF_TRACK_DEVICES,
                        default=self.hub.config.option_track_devices,
                    ): bool,
                    vol.Optional(
                        CONF_SSID_FILTER, default=selected_ssids_to_filter
                    ): cv.multi_select(ssid_filter),
                    vol.Optional(
                        CONF_DETECTION_TIME,
                        default=int(
                            self.hub.config.option_detection_time.total_seconds()
                        ),
                    ): int,
                    vol.Optional(
                        CONF_IGNORE_WIRED_BUG,
                        default=self.hub.config.option_ignore_wired_bug,
                    ): bool,
                }
            ),
            last_step=False,
        )