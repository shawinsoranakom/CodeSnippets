def test_broadcast_language_mapping(
    hass: HomeAssistant, setup_integration: ComponentSetup
) -> None:
    """Test all supported languages have a mapped broadcast command."""
    for language_code in SUPPORTED_LANGUAGE_CODES:
        cmds = broadcast_commands(language_code)
        assert cmds
        assert len(cmds) == 2
        assert cmds[0]
        assert "{0}" in cmds[0]
        assert "{1}" not in cmds[0]
        assert cmds[1]
        assert "{0}" in cmds[1]
        assert "{1}" in cmds[1]