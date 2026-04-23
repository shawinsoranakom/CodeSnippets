async def async_restore_traces(hass: HomeAssistant) -> None:
    """Restore saved traces."""
    if DATA_TRACES_RESTORED in hass.data:
        return

    hass.data[DATA_TRACES_RESTORED] = True

    store = hass.data[DATA_TRACE_STORE]
    try:
        restored_traces = await store.async_load() or {}
    except HomeAssistantError:
        _LOGGER.exception("Error loading traces")
        restored_traces = {}

    for key, traces in restored_traces.items():
        # Add stored traces in reversed order to prioritize the newest traces
        for json_trace in reversed(traces):
            if (
                (stored_traces := hass.data[DATA_TRACE].get(key))
                and stored_traces.size_limit is not None
                and len(stored_traces) >= stored_traces.size_limit
            ):
                break

            try:
                trace = RestoredTrace(json_trace)
            # Catch any exception to not blow up if the stored trace is invalid
            except Exception:
                _LOGGER.exception("Failed to restore trace")
                continue
            _async_store_restored_trace(hass, trace)