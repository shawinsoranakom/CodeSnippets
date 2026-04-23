async def test_arm_disarm_disarm(hass: HomeAssistant) -> None:
    """Test ArmDisarm trait Disarming support for alarm_control_panel domain."""
    assert helpers.get_google_type(alarm_control_panel.DOMAIN, None) is not None
    assert trait.ArmDisArmTrait.supported(alarm_control_panel.DOMAIN, 0, None, None)
    assert trait.ArmDisArmTrait.might_2fa(alarm_control_panel.DOMAIN, 0, None)

    trt = trait.ArmDisArmTrait(
        hass,
        State(
            "alarm_control_panel.alarm",
            AlarmControlPanelState.DISARMED,
            {
                alarm_control_panel.ATTR_CODE_ARM_REQUIRED: True,
                ATTR_SUPPORTED_FEATURES: AlarmControlPanelEntityFeature.TRIGGER
                | AlarmControlPanelEntityFeature.ARM_HOME
                | AlarmControlPanelEntityFeature.ARM_AWAY,
            },
        ),
        PIN_CONFIG,
    )
    assert trt.sync_attributes() == {
        "availableArmLevels": {
            "levels": [
                {
                    "level_name": "armed_home",
                    "level_values": [
                        {
                            "level_synonym": ["armed home", "home"],
                            "lang": "en",
                        }
                    ],
                },
                {
                    "level_name": "armed_away",
                    "level_values": [
                        {
                            "level_synonym": ["armed away", "away"],
                            "lang": "en",
                        }
                    ],
                },
                {
                    "level_name": "triggered",
                    "level_values": [{"level_synonym": ["triggered"], "lang": "en"}],
                },
            ],
            "ordered": True,
        }
    }

    assert trt.query_attributes() == {
        "currentArmLevel": "armed_home",
        "isArmed": False,
    }

    assert trt.can_execute(trait.COMMAND_ARM_DISARM, {"arm": False})

    calls = async_mock_service(
        hass, alarm_control_panel.DOMAIN, alarm_control_panel.SERVICE_ALARM_DISARM
    )

    # Test without secure_pin configured
    trt = trait.ArmDisArmTrait(
        hass,
        State(
            "alarm_control_panel.alarm",
            AlarmControlPanelState.ARMED_AWAY,
            {alarm_control_panel.ATTR_CODE_ARM_REQUIRED: True},
        ),
        BASIC_CONFIG,
    )
    with pytest.raises(error.SmartHomeError) as err:
        await trt.execute(trait.COMMAND_ARM_DISARM, BASIC_DATA, {"arm": False}, {})

    assert len(calls) == 0
    assert err.value.code == const.ERR_CHALLENGE_NOT_SETUP

    trt = trait.ArmDisArmTrait(
        hass,
        State(
            "alarm_control_panel.alarm",
            AlarmControlPanelState.ARMED_AWAY,
            {alarm_control_panel.ATTR_CODE_ARM_REQUIRED: True},
        ),
        PIN_CONFIG,
    )

    # No challenge data
    with pytest.raises(error.ChallengeNeeded) as err:
        await trt.execute(trait.COMMAND_ARM_DISARM, PIN_DATA, {"arm": False}, {})
    assert len(calls) == 0
    assert err.value.code == const.ERR_CHALLENGE_NEEDED
    assert err.value.challenge_type == const.CHALLENGE_PIN_NEEDED

    # invalid pin
    with pytest.raises(error.ChallengeNeeded) as err:
        await trt.execute(
            trait.COMMAND_ARM_DISARM, PIN_DATA, {"arm": False}, {"pin": 9999}
        )
    assert len(calls) == 0
    assert err.value.code == const.ERR_CHALLENGE_NEEDED
    assert err.value.challenge_type == const.CHALLENGE_FAILED_PIN_NEEDED

    # correct pin
    await trt.execute(
        trait.COMMAND_ARM_DISARM, PIN_DATA, {"arm": False}, {"pin": "1234"}
    )

    assert len(calls) == 1

    # Test already disarmed
    trt = trait.ArmDisArmTrait(
        hass,
        State(
            "alarm_control_panel.alarm",
            AlarmControlPanelState.DISARMED,
            {alarm_control_panel.ATTR_CODE_ARM_REQUIRED: True},
        ),
        PIN_CONFIG,
    )
    with pytest.raises(error.SmartHomeError) as err:
        await trt.execute(trait.COMMAND_ARM_DISARM, PIN_DATA, {"arm": False}, {})
    assert len(calls) == 1
    assert err.value.code == const.ERR_ALREADY_DISARMED

    trt = trait.ArmDisArmTrait(
        hass,
        State(
            "alarm_control_panel.alarm",
            AlarmControlPanelState.ARMED_AWAY,
            {alarm_control_panel.ATTR_CODE_ARM_REQUIRED: False},
        ),
        PIN_CONFIG,
    )

    # Cancel arming after already armed will require pin
    with pytest.raises(error.SmartHomeError) as err:
        await trt.execute(
            trait.COMMAND_ARM_DISARM, PIN_DATA, {"arm": True, "cancel": True}, {}
        )
    assert len(calls) == 1
    assert err.value.code == const.ERR_CHALLENGE_NEEDED
    assert err.value.challenge_type == const.CHALLENGE_PIN_NEEDED

    # Cancel arming while pending to arm doesn't require pin
    trt = trait.ArmDisArmTrait(
        hass,
        State(
            "alarm_control_panel.alarm",
            AlarmControlPanelState.PENDING,
            {alarm_control_panel.ATTR_CODE_ARM_REQUIRED: False},
        ),
        PIN_CONFIG,
    )
    await trt.execute(
        trait.COMMAND_ARM_DISARM, PIN_DATA, {"arm": True, "cancel": True}, {}
    )
    assert len(calls) == 2