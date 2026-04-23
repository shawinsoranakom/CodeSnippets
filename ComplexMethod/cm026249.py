def async_on_service_call(self, service: HomeassistantServiceCall) -> None:
        """Call service when user automation in ESPHome config is triggered."""
        hass = self.hass
        domain, service_name = service.service.split(".", 1)
        service_data = service.data

        if service.data_template:
            try:
                data_template = {
                    key: Template(value, hass)
                    for key, value in service.data_template.items()
                }
                service_data.update(
                    template.render_complex(data_template, service.variables)
                )
            except TemplateError as ex:
                _LOGGER.error(
                    "Error rendering data template %s for %s: %s",
                    service.data_template,
                    self.host,
                    ex,
                )
                return

        if service.is_event:
            device_id = self.device_id
            # ESPHome uses service call packet for both events and service calls
            # Ensure the user can only send events of form 'esphome.xyz'
            if domain != DOMAIN:
                _LOGGER.error(
                    "Can only generate events under esphome domain! (%s)", self.host
                )
                return

            # Call native tag scan
            if service_name == "tag_scanned" and device_id is not None:
                tag_id = service_data["tag_id"]
                hass.async_create_task(tag.async_scan_tag(hass, tag_id, device_id))
                return

            hass.bus.async_fire(
                service.service,
                {
                    ATTR_DEVICE_ID: device_id,
                    **service_data,
                },
            )
        elif self.entry.options.get(
            CONF_ALLOW_SERVICE_CALLS, DEFAULT_ALLOW_SERVICE_CALLS
        ):
            call_id = service.call_id
            if call_id and service.wants_response:
                # Service call with response expected
                self.entry.async_create_task(
                    hass,
                    self._handle_service_call_with_response(
                        domain,
                        service_name,
                        service_data,
                        call_id,
                        service.response_template,
                    ),
                )
            elif call_id:
                # Service call without response but needs success/failure notification
                self.entry.async_create_task(
                    hass,
                    self._handle_service_call_with_notification(
                        domain, service_name, service_data, call_id
                    ),
                )
            else:
                # Fire and forget service call
                self.entry.async_create_task(
                    hass, hass.services.async_call(domain, service_name, service_data)
                )
        else:
            device_info = self.entry_data.device_info
            assert device_info is not None
            async_create_issue(
                hass,
                DOMAIN,
                self.services_issue,
                is_fixable=False,
                severity=IssueSeverity.WARNING,
                translation_key="service_calls_not_allowed",
                translation_placeholders={
                    "name": device_info.friendly_name or device_info.name,
                },
            )
            _LOGGER.error(
                "%s: Service call %s.%s: with data %s rejected; "
                "If you trust this device and want to allow access for it to make "
                "Home Assistant service calls, you can enable this "
                "functionality in the options flow",
                device_info.friendly_name or device_info.name,
                domain,
                service_name,
                service_data,
            )