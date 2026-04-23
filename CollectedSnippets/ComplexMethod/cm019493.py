async def test_toggle(player) -> None:
    """Test the toggle method."""
    assert player.state == STATE_OFF
    await player.async_toggle()
    assert player.state == STATE_ON
    await player.async_toggle()
    assert player.state == STATE_OFF
    player.standby()
    assert player.state == STATE_STANDBY
    await player.async_toggle()
    assert player.state == STATE_ON
    player.idle()
    assert player.state == STATE_IDLE
    await player.async_toggle()
    assert player.state == STATE_OFF