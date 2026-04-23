async def test_arm_disarm_arm_away(hass: HomeAssistant) -> None:
    """Test ArmDisarm trait Arming support for alarm_control_panel domain."""
    assert helpers.get_google_type(alarm_control_panel.DOMAIN, None) is not None
    assert trait.ArmDisArmTrait.supported(alarm_control_panel.DOMAIN, 0, None, None)
    assert trait.ArmDisArmTrait.might_2fa(alarm_control_panel.DOMAIN, 0, None)

    trt = trait.ArmDisArmTrait(
        hass,
        State(
            "alarm_control_panel.alarm",
            AlarmControlPanelState.ARMED_AWAY,
            {
                alarm_control_panel.ATTR_CODE_ARM_REQUIRED: True,
                ATTR_SUPPORTED_FEATURES: AlarmControlPanelEntityFeature.ARM_HOME
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
                        {"level_synonym": ["armed home", "home"], "lang": "en"}
                    ],
                },
                {
                    "level_name": "armed_away",
                    "level_values": [
                        {"level_synonym": ["armed away", "away"], "lang": "en"}
                    ],
                },
            ],
            "ordered": True,
        }
    }

    assert trt.query_attributes() == {
        "isArmed": True,
        "currentArmLevel": AlarmControlPanelState.ARMED_AWAY,
    }

    assert trt.can_execute(
        trait.COMMAND_ARM_DISARM,
        {"arm": True, "armLevel": AlarmControlPanelState.ARMED_AWAY},
    )

    calls = async_mock_service(
        hass, alarm_control_panel.DOMAIN, alarm_control_panel.SERVICE_ALARM_ARM_AWAY
    )

    # Test with no secure_pin configured

    trt = trait.ArmDisArmTrait(
        hass,
        State(
            "alarm_control_panel.alarm",
            AlarmControlPanelState.DISARMED,
            {alarm_control_panel.ATTR_CODE_ARM_REQUIRED: True},
        ),
        BASIC_CONFIG,
    )
    with pytest.raises(error.SmartHomeError) as err:
        await trt.execute(
            trait.COMMAND_ARM_DISARM,
            BASIC_DATA,
            {"arm": True, "armLevel": AlarmControlPanelState.ARMED_AWAY},
            {},
        )
    assert len(calls) == 0
    assert err.value.code == const.ERR_CHALLENGE_NOT_SETUP

    trt = trait.ArmDisArmTrait(
        hass,
        State(
            "alarm_control_panel.alarm",
            AlarmControlPanelState.DISARMED,
            {alarm_control_panel.ATTR_CODE_ARM_REQUIRED: True},
        ),
        PIN_CONFIG,
    )
    # No challenge data
    with pytest.raises(error.ChallengeNeeded) as err:
        await trt.execute(
            trait.COMMAND_ARM_DISARM,
            PIN_DATA,
            {"arm": True, "armLevel": AlarmControlPanelState.ARMED_AWAY},
            {},
        )
    assert len(calls) == 0
    assert err.value.code == const.ERR_CHALLENGE_NEEDED
    assert err.value.challenge_type == const.CHALLENGE_PIN_NEEDED

    # invalid pin
    with pytest.raises(error.ChallengeNeeded) as err:
        await trt.execute(
            trait.COMMAND_ARM_DISARM,
            PIN_DATA,
            {"arm": True, "armLevel": AlarmControlPanelState.ARMED_AWAY},
            {"pin": 9999},
        )
    assert len(calls) == 0
    assert err.value.code == const.ERR_CHALLENGE_NEEDED
    assert err.value.challenge_type == const.CHALLENGE_FAILED_PIN_NEEDED

    # correct pin
    await trt.execute(
        trait.COMMAND_ARM_DISARM,
        PIN_DATA,
        {"arm": True, "armLevel": AlarmControlPanelState.ARMED_AWAY},
        {"pin": "1234"},
    )

    assert len(calls) == 1

    # Test already armed
    trt = trait.ArmDisArmTrait(
        hass,
        State(
            "alarm_control_panel.alarm",
            AlarmControlPanelState.ARMED_AWAY,
            {alarm_control_panel.ATTR_CODE_ARM_REQUIRED: True},
        ),
        PIN_CONFIG,
    )
    with pytest.raises(error.SmartHomeError) as err:
        await trt.execute(
            trait.COMMAND_ARM_DISARM,
            PIN_DATA,
            {"arm": True, "armLevel": AlarmControlPanelState.ARMED_AWAY},
            {},
        )
    assert len(calls) == 1
    assert err.value.code == const.ERR_ALREADY_ARMED

    # Test with code_arm_required False
    trt = trait.ArmDisArmTrait(
        hass,
        State(
            "alarm_control_panel.alarm",
            AlarmControlPanelState.DISARMED,
            {alarm_control_panel.ATTR_CODE_ARM_REQUIRED: False},
        ),
        PIN_CONFIG,
    )
    await trt.execute(
        trait.COMMAND_ARM_DISARM,
        PIN_DATA,
        {"arm": True, "armLevel": AlarmControlPanelState.ARMED_AWAY},
        {},
    )
    assert len(calls) == 2

    with pytest.raises(error.SmartHomeError) as err:
        await trt.execute(
            trait.COMMAND_ARM_DISARM,
            PIN_DATA,
            {"arm": True},
            {},
        )