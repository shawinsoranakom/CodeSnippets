def test_set_get_delete_token(hass: HomeAssistant) -> None:
    """Test set, get and delete token."""
    open_mock = mock_open()
    with patch(
        "homeassistant.components.remember_the_milk.storage.Path.open", open_mock
    ):
        config = rtm.RememberTheMilkConfiguration(hass)
        assert open_mock.return_value.write.call_count == 0
        assert config.get_token(PROFILE) is None
        assert open_mock.return_value.write.call_count == 0
        config.set_token(PROFILE, TOKEN)
        assert open_mock.return_value.write.call_count == 1
        assert open_mock.return_value.write.call_args[0][0] == json.dumps(
            {
                "myprofile": {
                    "id_map": {},
                    "token": "mytoken",
                }
            }
        )
        assert config.get_token(PROFILE) == TOKEN
        assert open_mock.return_value.write.call_count == 1
        config.delete_token(PROFILE)
        assert open_mock.return_value.write.call_count == 2
        assert open_mock.return_value.write.call_args[0][0] == json.dumps({})
        assert config.get_token(PROFILE) is None
        assert open_mock.return_value.write.call_count == 2