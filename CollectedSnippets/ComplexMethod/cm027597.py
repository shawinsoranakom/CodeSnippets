def async_translate_state(
    hass: HomeAssistant,
    state: str,
    domain: str,
    platform: str | None,
    translation_key: str | None,
    device_class: str | None,
) -> str:
    """Translate provided state using cached translations for currently selected language."""
    if state in [STATE_UNAVAILABLE, STATE_UNKNOWN]:
        return state
    language = hass.config.language
    if platform is not None and translation_key is not None:
        localize_key = (
            f"component.{platform}.entity.{domain}.{translation_key}.state.{state}"
        )
        translations = async_get_cached_translations(hass, language, "entity")
        if localize_key in translations:
            return translations[localize_key]

    translations = async_get_cached_translations(hass, language, "entity_component")
    if device_class is not None:
        localize_key = (
            f"component.{domain}.entity_component.{device_class}.state.{state}"
        )
        if localize_key in translations:
            return translations[localize_key]
    localize_key = f"component.{domain}.entity_component._.state.{state}"
    if localize_key in translations:
        return translations[localize_key]

    return state