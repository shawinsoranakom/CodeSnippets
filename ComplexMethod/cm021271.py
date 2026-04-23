def test_default_language_code(hass: HomeAssistant) -> None:
    """Test default_language_code."""
    assert default_language_code(hass) == "en-US"

    hass.config.language = "en"
    hass.config.country = "US"
    assert default_language_code(hass) == "en-US"

    hass.config.language = "en"
    hass.config.country = "GB"
    assert default_language_code(hass) == "en-GB"

    hass.config.language = "en"
    hass.config.country = "ES"
    assert default_language_code(hass) == "en-US"

    hass.config.language = "es"
    hass.config.country = "ES"
    assert default_language_code(hass) == "es-ES"

    hass.config.language = "es"
    hass.config.country = "MX"
    assert default_language_code(hass) == "es-MX"

    hass.config.language = "es"
    hass.config.country = None
    assert default_language_code(hass) == "es-ES"

    hass.config.language = "el"
    hass.config.country = "GR"
    assert default_language_code(hass) == "en-US"