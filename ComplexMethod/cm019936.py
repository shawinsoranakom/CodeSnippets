async def test_profile_load_optional_hs_color(hass: HomeAssistant) -> None:
    """Test profile loading with profiles containing no xy color."""

    csv_file = """the first line is skipped
no_color,,,100,1
no_color_no_transition,,,110
color,0.5119,0.4147,120,2
color_no_transition,0.4448,0.4066,130
color_and_brightness,0.4448,0.4066,170,
only_brightness,,,140
only_transition,,,,150
transition_float,,,,1.6
invalid_profile_1,
invalid_color_2,,0.1,1,2
invalid_color_3,,0.1,1
invalid_color_4,0.1,,1,3
invalid_color_5,0.1,,1
invalid_brightness,0,0,256,4
invalid_brightness_2,0,0,256
invalid_no_brightness_no_color_no_transition,,,
"""

    profiles = orig_Profiles(hass)
    with patch("builtins.open", mock_open(read_data=csv_file)):
        await profiles.async_initialize()
        await hass.async_block_till_done()

    assert profiles.data["no_color"].hs_color is None
    assert profiles.data["no_color"].brightness == 100
    assert profiles.data["no_color"].transition == 1

    assert profiles.data["no_color_no_transition"].hs_color is None
    assert profiles.data["no_color_no_transition"].brightness == 110
    assert profiles.data["no_color_no_transition"].transition is None

    assert profiles.data["color"].hs_color == (35.932, 69.412)
    assert profiles.data["color"].brightness == 120
    assert profiles.data["color"].transition == 2

    assert profiles.data["color_no_transition"].hs_color == (38.88, 49.02)
    assert profiles.data["color_no_transition"].brightness == 130
    assert profiles.data["color_no_transition"].transition is None

    assert profiles.data["color_and_brightness"].hs_color == (38.88, 49.02)
    assert profiles.data["color_and_brightness"].brightness == 170
    assert profiles.data["color_and_brightness"].transition is None

    assert profiles.data["only_brightness"].hs_color is None
    assert profiles.data["only_brightness"].brightness == 140
    assert profiles.data["only_brightness"].transition is None

    assert profiles.data["only_transition"].hs_color is None
    assert profiles.data["only_transition"].brightness is None
    assert profiles.data["only_transition"].transition == 150

    assert profiles.data["transition_float"].hs_color is None
    assert profiles.data["transition_float"].brightness is None
    assert profiles.data["transition_float"].transition == 1.6

    for invalid_profile_name in (
        "invalid_profile_1",
        "invalid_color_2",
        "invalid_color_3",
        "invalid_color_4",
        "invalid_color_5",
        "invalid_brightness",
        "invalid_brightness_2",
        "invalid_no_brightness_no_color_no_transition",
    ):
        assert invalid_profile_name not in profiles.data