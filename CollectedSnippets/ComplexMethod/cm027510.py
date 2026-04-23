async def async_step_ssdp(
        self, discovery_info: SsdpServiceInfo
    ) -> ConfigFlowResult:
        """Handle SSDP initiated config flow."""

        if TYPE_CHECKING:
            assert discovery_info.ssdp_location
        url = url_normalize(
            discovery_info.upnp.get(ATTR_UPNP_PRESENTATION_URL)
            or f"http://{urlparse(discovery_info.ssdp_location).hostname}/"
        )
        if TYPE_CHECKING:
            # url_normalize only returns None if passed None, and we don't do that
            assert url is not None

        upnp_udn = discovery_info.upnp.get(ATTR_UPNP_UDN)
        unique_id = discovery_info.upnp.get(ATTR_UPNP_SERIAL, upnp_udn)
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured(
            updates={CONF_UPNP_UDN: upnp_udn, CONF_URL: url}
        )

        def _is_supported_device() -> bool:
            """See if we are looking at a possibly supported device.

            Matching solely on SSDP data does not yield reliable enough results.
            """
            try:
                with Connection(url=url, timeout=CONNECTION_TIMEOUT) as conn:
                    basic_info = Client(conn).device.basic_information()
            except ResponseErrorException:  # API compatible error
                return True
            except Exception:  # API incompatible error # noqa: BLE001
                return False
            return isinstance(basic_info, dict)  # Crude content check

        if not await self.hass.async_add_executor_job(_is_supported_device):
            return self.async_abort(reason="unsupported_device")

        self.context.update(
            {
                "title_placeholders": {
                    CONF_NAME: (
                        discovery_info.upnp.get(ATTR_UPNP_MODEL_NAME)
                        or discovery_info.upnp.get(ATTR_UPNP_FRIENDLY_NAME)
                        or "Huawei LTE"
                    )
                }
            }
        )
        self.manufacturer = discovery_info.upnp.get(ATTR_UPNP_MANUFACTURER)
        self.upnp_udn = upnp_udn
        self.url = url
        return await self._async_show_user_form()