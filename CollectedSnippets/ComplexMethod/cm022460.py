async def test_lock_unlock_unlock(hass: HomeAssistant) -> None:
    """Test LockUnlock trait unlocking support for lock domain."""
    assert helpers.get_google_type(lock.DOMAIN, None) is not None
    assert trait.LockUnlockTrait.supported(
        lock.DOMAIN, LockEntityFeature.OPEN, None, None
    )

    trt = trait.LockUnlockTrait(
        hass, State("lock.front_door", lock.LockState.LOCKED), PIN_CONFIG
    )

    assert trt.sync_attributes() == {}

    assert trt.query_attributes() == {"isLocked": True}

    assert trt.can_execute(trait.COMMAND_LOCK_UNLOCK, {"lock": False})

    calls = async_mock_service(hass, lock.DOMAIN, lock.SERVICE_UNLOCK)

    # No challenge data
    with pytest.raises(error.ChallengeNeeded) as err:
        await trt.execute(trait.COMMAND_LOCK_UNLOCK, PIN_DATA, {"lock": False}, {})
    assert len(calls) == 0
    assert err.value.code == const.ERR_CHALLENGE_NEEDED
    assert err.value.challenge_type == const.CHALLENGE_PIN_NEEDED

    # invalid pin
    with pytest.raises(error.ChallengeNeeded) as err:
        await trt.execute(
            trait.COMMAND_LOCK_UNLOCK, PIN_DATA, {"lock": False}, {"pin": 9999}
        )
    assert len(calls) == 0
    assert err.value.code == const.ERR_CHALLENGE_NEEDED
    assert err.value.challenge_type == const.CHALLENGE_FAILED_PIN_NEEDED

    await trt.execute(
        trait.COMMAND_LOCK_UNLOCK, PIN_DATA, {"lock": False}, {"pin": "1234"}
    )

    assert len(calls) == 1
    assert calls[0].data == {ATTR_ENTITY_ID: "lock.front_door"}

    # Test without pin
    trt = trait.LockUnlockTrait(
        hass, State("lock.front_door", lock.LockState.LOCKED), BASIC_CONFIG
    )

    with pytest.raises(error.SmartHomeError) as err:
        await trt.execute(trait.COMMAND_LOCK_UNLOCK, BASIC_DATA, {"lock": False}, {})
    assert len(calls) == 1
    assert err.value.code == const.ERR_CHALLENGE_NOT_SETUP

    # Test with 2FA override
    with patch.object(
        BASIC_CONFIG,
        "should_2fa",
        return_value=False,
    ):
        await trt.execute(trait.COMMAND_LOCK_UNLOCK, BASIC_DATA, {"lock": False}, {})
    assert len(calls) == 2