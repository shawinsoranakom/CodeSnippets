def test_default_values():
    """Test the default values of the settings model."""
    fields = Settings.model_fields
    assert fields["TEST_MODE"].default is False
    assert fields["DEBUG_MODE"].default is False
    assert fields["DEV_BACKEND"].default is False
    assert fields["FILE_OVERWRITE"].default is False
    assert fields["SHOW_VERSION"].default is True
    assert fields["USE_INTERACTIVE_DF"].default is True
    assert fields["USE_CLEAR_AFTER_CMD"].default is False
    assert fields["USE_DATETIME"].default is True
    assert fields["USE_PROMPT_TOOLKIT"].default is True
    assert fields["ENABLE_EXIT_AUTO_HELP"].default is True
    assert fields["ENABLE_RICH_PANEL"].default is True
    assert fields["TOOLBAR_HINT"].default is True
    assert fields["SHOW_MSG_OBBJECT_REGISTRY"].default is False
    assert fields["TIMEZONE"].default == "America/New_York"
    assert fields["FLAIR"].default == ":openbb"
    assert fields["PREVIOUS_USE"].default is False
    assert fields["N_TO_KEEP_OBBJECT_REGISTRY"].default == 10
    assert fields["N_TO_DISPLAY_OBBJECT_REGISTRY"].default == 5
    assert fields["RICH_STYLE"].default == "dark"
    assert fields["ALLOWED_NUMBER_OF_ROWS"].default == 20
    assert fields["ALLOWED_NUMBER_OF_COLUMNS"].default == 5
    assert fields["HUB_URL"].default == "https://my.openbb.co"
    assert fields["BASE_URL"].default == "https://payments.openbb.co"