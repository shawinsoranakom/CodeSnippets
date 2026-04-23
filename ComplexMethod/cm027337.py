async def _gmail_service(call: ServiceCall) -> None:
    """Call Google Mail service."""
    for entry in await _extract_gmail_config_entries(call):
        try:
            auth = entry.runtime_data
        except AttributeError as ex:
            raise ValueError(f"Config entry not loaded: {entry.entry_id}") from ex
        service = await auth.get_resource()

        _settings = {
            "enableAutoReply": call.data[ATTR_ENABLED],
            "responseSubject": call.data.get(ATTR_TITLE),
        }
        if contacts := call.data.get(ATTR_RESTRICT_CONTACTS):
            _settings["restrictToContacts"] = contacts
        if domain := call.data.get(ATTR_RESTRICT_DOMAIN):
            _settings["restrictToDomain"] = domain
        if _date := call.data.get(ATTR_START):
            _dt = datetime.combine(_date, datetime.min.time())
            _settings["startTime"] = _dt.timestamp() * 1000
        if _date := call.data.get(ATTR_END):
            _dt = datetime.combine(_date, datetime.min.time())
            _settings["endTime"] = (_dt + timedelta(days=1)).timestamp() * 1000
        if call.data[ATTR_PLAIN_TEXT]:
            _settings["responseBodyPlainText"] = call.data[ATTR_MESSAGE]
        else:
            _settings["responseBodyHtml"] = call.data[ATTR_MESSAGE]
        settings: HttpRequest = (
            service.users().settings().updateVacation(userId=ATTR_ME, body=_settings)
        )
        await call.hass.async_add_executor_job(settings.execute)