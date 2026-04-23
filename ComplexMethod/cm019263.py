async def test_state_reporting(hass: HomeAssistant) -> None:
    """Test the state reporting.

    The group state is unavailable if all group members are unavailable.
    Otherwise, the group state is unknown if all group members are unknown.
    Otherwise, the group state is buffering if all group members are buffering.
    Otherwise, the group state is idle if all group members are idle.
    Otherwise, the group state is paused if all group members are paused.
    Otherwise, the group state is playing if all group members are playing.
    Otherwise, the group state is on if at least one group member is not off, unavailable or unknown.
    Otherwise, the group state is off.
    """
    await async_setup_component(
        hass,
        MEDIA_DOMAIN,
        {
            MEDIA_DOMAIN: {
                "platform": DOMAIN,
                "entities": ["media_player.player_1", "media_player.player_2"],
            }
        },
    )
    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()

    # Initial state with no group member in the state machine -> unavailable
    assert hass.states.get("media_player.media_group").state == STATE_UNAVAILABLE

    # All group members unavailable -> unavailable
    hass.states.async_set("media_player.player_1", STATE_UNAVAILABLE)
    hass.states.async_set("media_player.player_2", STATE_UNAVAILABLE)
    await hass.async_block_till_done()
    assert hass.states.get("media_player.media_group").state == STATE_UNAVAILABLE

    # The group state is unknown if all group members are unknown or unavailable.
    for state_1 in (
        STATE_UNAVAILABLE,
        STATE_UNKNOWN,
    ):
        hass.states.async_set("media_player.player_1", state_1)
        hass.states.async_set("media_player.player_2", STATE_UNKNOWN)
        await hass.async_block_till_done()
        assert hass.states.get("media_player.media_group").state == STATE_UNKNOWN

    # All group members buffering -> buffering
    # All group members idle -> idle
    # All group members paused -> paused
    # All group members playing -> playing
    # All group members unavailable -> unavailable
    # All group members unknown -> unknown
    for state in (
        STATE_BUFFERING,
        STATE_IDLE,
        STATE_PAUSED,
        STATE_PLAYING,
        STATE_UNAVAILABLE,
        STATE_UNKNOWN,
    ):
        hass.states.async_set("media_player.player_1", state)
        hass.states.async_set("media_player.player_2", state)
        await hass.async_block_till_done()
        assert hass.states.get("media_player.media_group").state == state

    # At least one member not off, unavailable or unknown -> on
    for state_1 in (STATE_BUFFERING, STATE_IDLE, STATE_ON, STATE_PAUSED, STATE_PLAYING):
        for state_2 in (STATE_OFF, STATE_UNAVAILABLE, STATE_UNKNOWN):
            hass.states.async_set("media_player.player_1", state_1)
            hass.states.async_set("media_player.player_2", state_2)
            await hass.async_block_till_done()
            assert hass.states.get("media_player.media_group").state == STATE_ON

    # Otherwise off
    for state_1 in (STATE_OFF, STATE_UNAVAILABLE, STATE_UNKNOWN):
        hass.states.async_set("media_player.player_1", state_1)
        hass.states.async_set("media_player.player_2", STATE_OFF)
        await hass.async_block_till_done()
        assert hass.states.get("media_player.media_group").state == STATE_OFF

    # All group members in same invalid state -> unknown
    hass.states.async_set("media_player.player_1", "invalid_state")
    hass.states.async_set("media_player.player_2", "invalid_state")
    await hass.async_block_till_done()
    assert hass.states.get("media_player.media_group").state == STATE_UNKNOWN

    # All group members removed from the state machine -> unavailable
    hass.states.async_remove("media_player.player_1")
    hass.states.async_remove("media_player.player_2")
    await hass.async_block_till_done()
    assert hass.states.get("media_player.media_group").state == STATE_UNAVAILABLE