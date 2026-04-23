async def get(
        self,
        request: web.Request,
        d_type: str,
        d_id: str,
        sub_type: str | None = None,
        sub_id: str | None = None,
    ) -> web.Response:
        """Download diagnostics."""
        # Validate d_type and sub_type
        try:
            DiagnosticsType(d_type)
        except ValueError:
            return web.Response(status=HTTPStatus.BAD_REQUEST)

        if sub_type is not None:
            try:
                DiagnosticsSubType(sub_type)
            except ValueError:
                return web.Response(status=HTTPStatus.BAD_REQUEST)

        device_diagnostics = sub_type is not None

        hass = request.app[http.KEY_HASS]

        if (config_entry := hass.config_entries.async_get_entry(d_id)) is None:
            return web.Response(status=HTTPStatus.NOT_FOUND)

        diagnostics_data = hass.data[_DIAGNOSTICS_DATA]
        if (info := diagnostics_data.platforms.get(config_entry.domain)) is None:
            return web.Response(status=HTTPStatus.NOT_FOUND)

        filename = f"{config_entry.domain}-{config_entry.entry_id}"

        issue_registry = ir.async_get(hass)
        issues = issue_registry.issues
        data_issues = [
            issue_reg.to_json()
            for issue_id, issue_reg in issues.items()
            if issue_id[0] == config_entry.domain
        ]

        if not device_diagnostics:
            # Config entry diagnostics
            if info.config_entry_diagnostics is None:
                return web.Response(status=HTTPStatus.NOT_FOUND)
            data = await info.config_entry_diagnostics(hass, config_entry)
            filename = f"{DiagnosticsType.CONFIG_ENTRY}-{filename}"
            return await _async_get_json_file_response(
                hass, data, data_issues, filename, config_entry.domain, d_id
            )

        # Device diagnostics
        dev_reg = dr.async_get(hass)
        if sub_id is None:
            return web.Response(status=HTTPStatus.BAD_REQUEST)

        if (device := dev_reg.async_get(sub_id)) is None:
            return web.Response(status=HTTPStatus.NOT_FOUND)

        filename += f"-{device.name}-{device.id}"

        if info.device_diagnostics is None:
            return web.Response(status=HTTPStatus.NOT_FOUND)

        data = await info.device_diagnostics(hass, config_entry, device)
        return await _async_get_json_file_response(
            hass, data, data_issues, filename, config_entry.domain, d_id, sub_id
        )