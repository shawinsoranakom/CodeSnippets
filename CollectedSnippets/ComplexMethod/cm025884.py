async def async_setup_profiles(
        self, configure_unique_id: bool = True
    ) -> tuple[dict[str, str], dict[str, str]]:
        """Fetch ONVIF device profiles."""
        if LOGGER.isEnabledFor(logging.DEBUG):
            LOGGER.debug(
                "Fetching profiles from ONVIF device %s", pformat(self.onvif_config)
            )

        device = get_device(
            self.hass,
            self.onvif_config[CONF_HOST],
            self.onvif_config[CONF_PORT],
            self.onvif_config[CONF_USERNAME],
            self.onvif_config[CONF_PASSWORD],
        )

        try:
            await device.update_xaddrs()
            device_mgmt = await device.create_devicemgmt_service()
            # Get the MAC address to use as the unique ID for the config flow
            if not self.device_id:
                try:
                    network_interfaces = await device_mgmt.GetNetworkInterfaces()
                    interface = next(
                        filter(lambda interface: interface.Enabled, network_interfaces),
                        None,
                    )
                    if interface:
                        self.device_id = interface.Info.HwAddress
                except Fault as fault:
                    if "not implemented" not in fault.message:
                        raise
                    LOGGER.debug(
                        "%s: Could not get network interfaces: %s",
                        self.onvif_config[CONF_NAME],
                        stringify_onvif_error(fault),
                    )
            # If no network interfaces are exposed, fallback to serial number
            if not self.device_id:
                device_info = await device_mgmt.GetDeviceInformation()
                self.device_id = device_info.SerialNumber

            if not self.device_id:
                raise AbortFlow(reason="no_mac")

            if configure_unique_id:
                await self.async_set_unique_id(self.device_id, raise_on_progress=False)
                self._abort_if_unique_id_configured(
                    updates={
                        CONF_HOST: self.onvif_config[CONF_HOST],
                        CONF_PORT: self.onvif_config[CONF_PORT],
                        CONF_NAME: self.onvif_config[CONF_NAME],
                        CONF_USERNAME: self.onvif_config[CONF_USERNAME],
                        CONF_PASSWORD: self.onvif_config[CONF_PASSWORD],
                    }
                )
            # Verify there is an H264 profile
            media_service = await device.create_media_service()
            profiles = await media_service.GetProfiles()
        except AttributeError:  # Likely an empty document or 404 from the wrong port
            LOGGER.debug(
                "%s: No ONVIF service found at %s:%s",
                self.onvif_config[CONF_NAME],
                self.onvif_config[CONF_HOST],
                self.onvif_config[CONF_PORT],
                exc_info=True,
            )
            return {CONF_PORT: "no_onvif_service"}, {}
        except Fault as err:
            stringified_error = stringify_onvif_error(err)
            description_placeholders = {"error": stringified_error}
            if is_auth_error(err):
                LOGGER.debug(
                    "%s: Could not authenticate with camera: %s",
                    self.onvif_config[CONF_NAME],
                    stringified_error,
                )
                return {CONF_PASSWORD: "auth_failed"}, description_placeholders
            LOGGER.debug(
                "%s: Could not determine camera capabilities: %s",
                self.onvif_config[CONF_NAME],
                stringified_error,
                exc_info=True,
            )
            return {"base": "onvif_error"}, description_placeholders
        except GET_CAPABILITIES_EXCEPTIONS as err:
            LOGGER.debug(
                "%s: Could not determine camera capabilities: %s",
                self.onvif_config[CONF_NAME],
                stringify_onvif_error(err),
                exc_info=True,
            )
            return {"base": "onvif_error"}, {"error": stringify_onvif_error(err)}
        else:
            if not any(
                profile.VideoEncoderConfiguration
                and profile.VideoEncoderConfiguration.Encoding == "H264"
                for profile in profiles
            ):
                raise AbortFlow(reason="no_h264")
            return {}, {}
        finally:
            await device.close()