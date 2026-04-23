def test_validate_entity_config() -> None:
    """Test validate entities."""
    configs = [
        None,
        [],
        "string",
        12345,
        {"invalid_entity_id": {}},
        {"demo.test": 1},
        {"binary_sensor.demo": {CONF_LINKED_BATTERY_SENSOR: None}},
        {"binary_sensor.demo": {CONF_LINKED_BATTERY_SENSOR: "switch.demo"}},
        {"binary_sensor.demo": {CONF_LOW_BATTERY_THRESHOLD: "switch.demo"}},
        {"binary_sensor.demo": {CONF_LOW_BATTERY_THRESHOLD: -10}},
        {"demo.test": "test"},
        {"demo.test": [1, 2]},
        {"demo.test": None},
        {"demo.test": {CONF_NAME: None}},
        {"media_player.test": {CONF_FEATURE_LIST: [{CONF_FEATURE: "invalid_feature"}]}},
        {
            "media_player.test": {
                CONF_FEATURE_LIST: [
                    {CONF_FEATURE: FEATURE_ON_OFF},
                    {CONF_FEATURE: FEATURE_ON_OFF},
                ]
            }
        },
        {"switch.test": {CONF_TYPE: "invalid_type"}},
        {
            "switch.test": {
                CONF_TYPE: "sprinkler",
                CONF_LINKED_VALVE_DURATION: "number.valve_duration",  # Must be input_number entity
                CONF_LINKED_VALVE_END_TIME: "datetime.valve_end_time",  # Must be sensor (timestamp) entity
            }
        },
        {"fan.test": {CONF_TYPE: "invalid_type"}},
        {
            "valve.test": {
                CONF_LINKED_VALVE_END_TIME: "datetime.valve_end_time",  # Must be sensor (timestamp) entity
                CONF_LINKED_VALVE_DURATION: "number.valve_duration",  # Must be input_number
            }
        },
        {
            "valve.test": {
                CONF_TYPE: "sprinkler",  # Extra keys not allowed
            }
        },
    ]

    for conf in configs:
        with pytest.raises(vol.Invalid):
            vec(conf)

    assert vec({}) == {}
    assert vec({"demo.test": {CONF_NAME: "Name"}}) == {
        "demo.test": {CONF_NAME: "Name", CONF_LOW_BATTERY_THRESHOLD: 20}
    }

    assert vec(
        {"binary_sensor.demo": {CONF_LINKED_BATTERY_SENSOR: "sensor.demo_battery"}}
    ) == {
        "binary_sensor.demo": {
            CONF_LINKED_BATTERY_SENSOR: "sensor.demo_battery",
            CONF_LOW_BATTERY_THRESHOLD: 20,
        }
    }
    assert vec({"binary_sensor.demo": {CONF_LOW_BATTERY_THRESHOLD: 50}}) == {
        "binary_sensor.demo": {CONF_LOW_BATTERY_THRESHOLD: 50}
    }

    assert vec({"alarm_control_panel.demo": {}}) == {
        "alarm_control_panel.demo": {ATTR_CODE: None, CONF_LOW_BATTERY_THRESHOLD: 20}
    }
    assert vec({"alarm_control_panel.demo": {ATTR_CODE: "1234"}}) == {
        "alarm_control_panel.demo": {ATTR_CODE: "1234", CONF_LOW_BATTERY_THRESHOLD: 20}
    }

    assert vec({"lock.demo": {}}) == {
        "lock.demo": {ATTR_CODE: None, CONF_LOW_BATTERY_THRESHOLD: 20}
    }

    assert vec(
        {
            "lock.demo": {
                ATTR_CODE: "1234",
                CONF_LINKED_DOORBELL_SENSOR: "event.doorbell",
            }
        }
    ) == {
        "lock.demo": {
            ATTR_CODE: "1234",
            CONF_LOW_BATTERY_THRESHOLD: 20,
            CONF_LINKED_DOORBELL_SENSOR: "event.doorbell",
        }
    }

    assert vec({"media_player.demo": {}}) == {
        "media_player.demo": {CONF_FEATURE_LIST: {}, CONF_LOW_BATTERY_THRESHOLD: 20}
    }
    config = {
        CONF_FEATURE_LIST: [
            {CONF_FEATURE: FEATURE_ON_OFF},
            {CONF_FEATURE: FEATURE_PLAY_PAUSE},
        ]
    }
    assert vec({"media_player.demo": config}) == {
        "media_player.demo": {
            CONF_FEATURE_LIST: {FEATURE_ON_OFF: {}, FEATURE_PLAY_PAUSE: {}},
            CONF_LOW_BATTERY_THRESHOLD: 20,
        }
    }

    assert vec({"switch.demo": {CONF_TYPE: TYPE_FAUCET}}) == {
        "switch.demo": {CONF_TYPE: TYPE_FAUCET, CONF_LOW_BATTERY_THRESHOLD: 20}
    }
    assert vec({"switch.demo": {CONF_TYPE: TYPE_OUTLET}}) == {
        "switch.demo": {CONF_TYPE: TYPE_OUTLET, CONF_LOW_BATTERY_THRESHOLD: 20}
    }
    assert vec({"switch.demo": {CONF_TYPE: TYPE_SHOWER}}) == {
        "switch.demo": {CONF_TYPE: TYPE_SHOWER, CONF_LOW_BATTERY_THRESHOLD: 20}
    }
    assert vec({"switch.demo": {CONF_TYPE: TYPE_SPRINKLER}}) == {
        "switch.demo": {CONF_TYPE: TYPE_SPRINKLER, CONF_LOW_BATTERY_THRESHOLD: 20}
    }
    assert vec({"switch.demo": {CONF_TYPE: TYPE_SWITCH}}) == {
        "switch.demo": {CONF_TYPE: TYPE_SWITCH, CONF_LOW_BATTERY_THRESHOLD: 20}
    }
    assert vec({"switch.demo": {CONF_TYPE: TYPE_VALVE}}) == {
        "switch.demo": {CONF_TYPE: TYPE_VALVE, CONF_LOW_BATTERY_THRESHOLD: 20}
    }
    config = {
        CONF_TYPE: TYPE_SPRINKLER,
        CONF_LINKED_VALVE_DURATION: "input_number.valve_duration",
        CONF_LINKED_VALVE_END_TIME: "sensor.valve_end_time",
    }
    assert vec({"switch.sprinkler": config}) == {
        "switch.sprinkler": {
            CONF_TYPE: TYPE_SPRINKLER,
            CONF_LINKED_VALVE_DURATION: "input_number.valve_duration",
            CONF_LINKED_VALVE_END_TIME: "sensor.valve_end_time",
            CONF_LOW_BATTERY_THRESHOLD: DEFAULT_LOW_BATTERY_THRESHOLD,
        }
    }
    assert vec({"sensor.co": {CONF_THRESHOLD_CO: 500}}) == {
        "sensor.co": {CONF_THRESHOLD_CO: 500, CONF_LOW_BATTERY_THRESHOLD: 20}
    }
    assert vec({"sensor.co2": {CONF_THRESHOLD_CO2: 500}}) == {
        "sensor.co2": {CONF_THRESHOLD_CO2: 500, CONF_LOW_BATTERY_THRESHOLD: 20}
    }
    assert vec(
        {
            "camera.demo": {
                CONF_LINKED_DOORBELL_SENSOR: "event.doorbell",
                CONF_LINKED_MOTION_SENSOR: "event.motion",
            }
        }
    ) == {
        "camera.demo": {
            CONF_LINKED_DOORBELL_SENSOR: "event.doorbell",
            CONF_LINKED_MOTION_SENSOR: "event.motion",
            CONF_AUDIO_CODEC: DEFAULT_AUDIO_CODEC,
            CONF_SUPPORT_AUDIO: DEFAULT_SUPPORT_AUDIO,
            CONF_MAX_WIDTH: DEFAULT_MAX_WIDTH,
            CONF_MAX_HEIGHT: DEFAULT_MAX_HEIGHT,
            CONF_MAX_FPS: DEFAULT_MAX_FPS,
            CONF_AUDIO_MAP: DEFAULT_AUDIO_MAP,
            CONF_VIDEO_MAP: DEFAULT_VIDEO_MAP,
            CONF_STREAM_COUNT: DEFAULT_STREAM_COUNT,
            CONF_VIDEO_CODEC: DEFAULT_VIDEO_CODEC,
            CONF_VIDEO_PROFILE_NAMES: DEFAULT_VIDEO_PROFILE_NAMES,
            CONF_AUDIO_PACKET_SIZE: DEFAULT_AUDIO_PACKET_SIZE,
            CONF_VIDEO_PACKET_SIZE: DEFAULT_VIDEO_PACKET_SIZE,
            CONF_LOW_BATTERY_THRESHOLD: DEFAULT_LOW_BATTERY_THRESHOLD,
        }
    }
    config = {
        CONF_LINKED_VALVE_DURATION: "input_number.valve_duration",
        CONF_LINKED_VALVE_END_TIME: "sensor.valve_end_time",
    }
    assert vec({"valve.demo": config}) == {
        "valve.demo": {
            CONF_LINKED_VALVE_DURATION: "input_number.valve_duration",
            CONF_LINKED_VALVE_END_TIME: "sensor.valve_end_time",
            CONF_LOW_BATTERY_THRESHOLD: DEFAULT_LOW_BATTERY_THRESHOLD,
        }
    }