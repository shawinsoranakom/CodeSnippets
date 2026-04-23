async def _async_create_entry(self) -> ConfigFlowResult:
        """Create the config entry."""
        assert self._name is not None
        assert self._device_info is not None

        # Check if Z-Wave capabilities are present and start discovery flow
        next_flow_id: str | None = None
        # If the zwave_home_id is not set, we don't know if it's a fresh
        # adapter, or the cable is just unplugged. So only start
        # the zwave_js config flow automatically if there is a
        # zwave_home_id present. If it's a fresh adapter, the manager
        # will handle starting the flow once it gets the home id changed
        # request from the ESPHome device.
        if (
            self._device_info.zwave_proxy_feature_flags
            and self._device_info.zwave_home_id
        ):
            assert self._connected_address is not None
            assert self._port is not None

            # Start Z-Wave discovery flow and get the flow ID
            zwave_result = await self.hass.config_entries.flow.async_init(
                "zwave_js",
                context={
                    "source": SOURCE_ESPHOME,
                    "discovery_key": discovery_flow.DiscoveryKey(
                        domain=DOMAIN,
                        key=self._device_info.mac_address,
                        version=1,
                    ),
                },
                data=ESPHomeServiceInfo(
                    name=self._device_info.name,
                    zwave_home_id=self._device_info.zwave_home_id,
                    ip_address=self._connected_address,
                    port=self._port,
                    noise_psk=self._noise_psk,
                ),
            )
            if zwave_result["type"] in (
                FlowResultType.ABORT,
                FlowResultType.CREATE_ENTRY,
            ):
                _LOGGER.debug(
                    "Unable to continue created Z-Wave JS config flow: %s", zwave_result
                )
            else:
                next_flow_id = zwave_result["flow_id"]

        return self.async_create_entry(
            title=self._name,
            data=self._async_make_config_data(),
            options={
                CONF_ALLOW_SERVICE_CALLS: DEFAULT_NEW_CONFIG_ALLOW_ALLOW_SERVICE_CALLS,
            },
            next_flow=(FlowType.CONFIG_FLOW, next_flow_id) if next_flow_id else None,
        )