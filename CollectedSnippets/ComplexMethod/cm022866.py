def test_config_set_delete_id(hass: HomeAssistant) -> None:
    """Test setting and deleting an id from the config."""
    hass_id = "123"
    list_id = "1"
    timeseries_id = "2"
    rtm_id = "3"
    open_mock = mock_open()
    config = rtm.RememberTheMilkConfiguration(hass)
    with patch(
        "homeassistant.components.remember_the_milk.storage.Path.open", open_mock
    ):
        config = rtm.RememberTheMilkConfiguration(hass)
        assert open_mock.return_value.write.call_count == 0
        assert config.get_rtm_id(PROFILE, hass_id) is None
        assert open_mock.return_value.write.call_count == 0
        config.set_rtm_id(PROFILE, hass_id, list_id, timeseries_id, rtm_id)
        assert (list_id, timeseries_id, rtm_id) == config.get_rtm_id(PROFILE, hass_id)
        assert open_mock.return_value.write.call_count == 1
        assert open_mock.return_value.write.call_args[0][0] == json.dumps(
            {
                "myprofile": {
                    "id_map": {
                        "123": {"list_id": "1", "timeseries_id": "2", "task_id": "3"}
                    }
                }
            }
        )
        config.delete_rtm_id(PROFILE, hass_id)
        assert config.get_rtm_id(PROFILE, hass_id) is None
        assert open_mock.return_value.write.call_count == 2
        assert open_mock.return_value.write.call_args[0][0] == json.dumps(
            {
                "myprofile": {
                    "id_map": {},
                }
            }
        )