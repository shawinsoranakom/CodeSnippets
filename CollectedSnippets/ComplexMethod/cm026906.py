def _get_debug_targets(
    hass: HomeAssistant,
    result: RecognizeResult,
) -> Iterable[tuple[State, bool]]:
    """Yield state/is_matched pairs for a hassil recognition."""
    entities = result.entities

    name: str | None = None
    area_name: str | None = None
    domains: set[str] | None = None
    device_classes: set[str] | None = None
    state_names: set[str] | None = None

    if "name" in entities:
        name = str(entities["name"].value)

    if "area" in entities:
        area_name = str(entities["area"].value)

    if "domain" in entities:
        domains = set(cv.ensure_list(entities["domain"].value))

    if "device_class" in entities:
        device_classes = set(cv.ensure_list(entities["device_class"].value))

    if "state" in entities:
        # HassGetState only
        state_names = set(cv.ensure_list(entities["state"].value))

    if (
        (name is None)
        and (area_name is None)
        and (not domains)
        and (not device_classes)
        and (not state_names)
    ):
        # Avoid "matching" all entities when there is no filter
        return

    states = intent.async_match_states(
        hass,
        name=name,
        area_name=area_name,
        domains=domains,
        device_classes=device_classes,
    )

    for state in states:
        # For queries, a target is "matched" based on its state
        is_matched = (state_names is None) or (state.state in state_names)
        yield state, is_matched