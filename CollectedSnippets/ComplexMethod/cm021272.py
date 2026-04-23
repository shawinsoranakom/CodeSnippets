def test_best_matching_language_code(hass: HomeAssistant) -> None:
    """Test best_matching_language_code."""
    hass.config.language = "es"
    hass.config.country = "MX"

    # Assist Language is supported
    assert best_matching_language_code(hass, "de-DE", "en-AU") == "de-DE"
    assert best_matching_language_code(hass, "de-DE") == "de-DE"

    # Assist Language is not supported, but agent language has the same "lang" part, and is supported
    assert best_matching_language_code(hass, "en", "en-AU") == "en-AU"
    assert best_matching_language_code(hass, "en-XYZ", "en-AU") == "en-AU"
    # Assist Language is not supported, but agent language has the same "lang" part, but is not supported
    assert best_matching_language_code(hass, "en", "en-XYZ") == "en-US"
    assert best_matching_language_code(hass, "en-XYZ", "en-ABC") == "en-US"

    # Assist Language is not supported, agent is not matching or available, falling back to the default of assist lang
    assert best_matching_language_code(hass, "de", "en-AU") == "de-DE"
    assert best_matching_language_code(hass, "de-XYZ", "en-AU") == "de-DE"
    assert best_matching_language_code(hass, "de") == "de-DE"
    assert best_matching_language_code(hass, "de-XYZ") == "de-DE"

    # Assist language is not existing at all, agent is supported
    assert best_matching_language_code(hass, "abc-XYZ", "en-AU") == "en-AU"

    # Assist language is not existing at all, agent is not supported, falling back to the agent default
    assert best_matching_language_code(hass, "abc-XYZ", "de-XYZ") == "de-DE"

    # Assist language is not existing at all, agent is not existing or available, falling back to system default
    assert best_matching_language_code(hass, "abc-XYZ", "def-XYZ") == "es-MX"
    assert best_matching_language_code(hass, "abc-XYZ") == "es-MX"

    # Assist language is not existing at all, agent is not existing or available, system default is not supported
    hass.config.language = "el"
    hass.config.country = "GR"
    assert best_matching_language_code(hass, "abc-XYZ", "def-XYZ") == "en-US"
    assert best_matching_language_code(hass, "abc-XYZ") == "en-US"