async def test_zgs_event_group_speakers(
    hass: HomeAssistant, sonos_setup_two_speakers: list[MockSoCo]
) -> None:
    """Tests grouping and ungrouping two speakers."""
    # When Sonos speakers are grouped; one of the speakers is the coordinator and is in charge
    # of playback across both speakers. Hence, service calls to play or pause on media_players
    # that are part of the group are routed to the coordinator.
    soco_lr = sonos_setup_two_speakers[0]
    soco_br = sonos_setup_two_speakers[1]

    # Test 1 - Initial state - speakers are not grouped
    state = hass.states.get("media_player.living_room")
    assert state.attributes["group_members"] == ["media_player.living_room"]
    state = hass.states.get("media_player.bedroom")
    assert state.attributes["group_members"] == ["media_player.bedroom"]
    # Each speaker is its own coordinator and calls should route to their SoCos
    await _media_play(hass, "media_player.living_room")
    assert soco_lr.play.call_count == 1
    await _media_play(hass, "media_player.bedroom")
    assert soco_br.play.call_count == 1

    soco_lr.play.reset_mock()
    soco_br.play.reset_mock()

    # Test 2 - Group the speakers, living room is the coordinator
    group_speakers(soco_lr, soco_br)

    await hass.async_block_till_done(wait_background_tasks=True)
    state = hass.states.get("media_player.living_room")
    assert state.attributes["group_members"] == [
        "media_player.living_room",
        "media_player.bedroom",
    ]
    state = hass.states.get("media_player.bedroom")
    assert state.attributes["group_members"] == [
        "media_player.living_room",
        "media_player.bedroom",
    ]
    # Play calls should route to the living room SoCo
    await _media_play(hass, "media_player.living_room")
    await _media_play(hass, "media_player.bedroom")
    assert soco_lr.play.call_count == 2
    assert soco_br.play.call_count == 0

    soco_lr.play.reset_mock()
    soco_br.play.reset_mock()

    # Test 3 - Ungroup the speakers
    ungroup_speakers(soco_lr, soco_br)

    await hass.async_block_till_done(wait_background_tasks=True)
    state = hass.states.get("media_player.living_room")
    assert state.attributes["group_members"] == ["media_player.living_room"]
    state = hass.states.get("media_player.bedroom")
    assert state.attributes["group_members"] == ["media_player.bedroom"]
    # Calls should route to each speakers Soco
    await _media_play(hass, "media_player.living_room")
    assert soco_lr.play.call_count == 1
    await _media_play(hass, "media_player.bedroom")
    assert soco_br.play.call_count == 1