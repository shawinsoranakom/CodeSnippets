async def test_acknowledge(
    hass: HomeAssistant,
    init_components,
    pipeline_data: assist_pipeline.pipeline.PipelineData,
    mock_chat_session: chat_session.ChatSession,
    entity_registry: er.EntityRegistry,
    area_registry: ar.AreaRegistry,
    device_registry: dr.DeviceRegistry,
    use_satellite_entity: bool,
) -> None:
    """Test that acknowledge sound is played when targets are in the same area."""
    area_1 = area_registry.async_get_or_create("area_1")

    light_1 = entity_registry.async_get_or_create(
        "light", "demo", "1234", original_name="light 1"
    )
    hass.states.async_set(light_1.entity_id, "off", {ATTR_FRIENDLY_NAME: "light 1"})
    light_1 = entity_registry.async_update_entity(light_1.entity_id, area_id=area_1.id)

    light_2 = entity_registry.async_get_or_create(
        "light", "demo", "5678", original_name="light 2"
    )
    hass.states.async_set(light_2.entity_id, "off", {ATTR_FRIENDLY_NAME: "light 2"})
    light_2 = entity_registry.async_update_entity(light_2.entity_id, area_id=area_1.id)

    entry = MockConfigEntry()
    entry.add_to_hass(hass)

    satellite = entity_registry.async_get_or_create("assist_satellite", "test", "1234")
    entity_registry.async_update_entity(satellite.entity_id, area_id=area_1.id)

    satellite_device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections=set(),
        identifiers={("demo", "id-1234")},
    )
    device_registry.async_update_device(satellite_device.id, area_id=area_1.id)

    events: list[assist_pipeline.PipelineEvent] = []
    turn_on = async_mock_service(hass, "light", "turn_on")

    pipeline_store = pipeline_data.pipeline_store
    pipeline_id = pipeline_store.async_get_preferred_item()
    pipeline = assist_pipeline.pipeline.async_get_pipeline(hass, pipeline_id)

    async def _run(text: str) -> None:
        pipeline_input = assist_pipeline.pipeline.PipelineInput(
            intent_input=text,
            session=mock_chat_session,
            satellite_id=satellite.entity_id if use_satellite_entity else None,
            device_id=satellite_device.id if not use_satellite_entity else None,
            run=assist_pipeline.pipeline.PipelineRun(
                hass,
                context=Context(),
                pipeline=pipeline,
                start_stage=assist_pipeline.PipelineStage.INTENT,
                end_stage=assist_pipeline.PipelineStage.TTS,
                event_callback=events.append,
            ),
        )
        await pipeline_input.validate()
        await pipeline_input.execute()

    with patch(
        "homeassistant.components.assist_pipeline.PipelineRun.text_to_speech"
    ) as text_to_speech:

        def _reset() -> None:
            events.clear()
            text_to_speech.reset_mock()
            turn_on.clear()

        # 1. All targets in same area
        await _run("turn on the lights")

        # Acknowledgment sound should be played (same area)
        text_to_speech.assert_called_once()
        assert (
            text_to_speech.call_args.kwargs["override_media_path"] == ACKNOWLEDGE_PATH
        )
        assert len(turn_on) == 2

        # 2. One light in a different area
        area_2 = area_registry.async_get_or_create("area_2")
        light_2 = entity_registry.async_update_entity(
            light_2.entity_id, area_id=area_2.id
        )

        _reset()
        await _run("turn on light 2")

        # Acknowledgment sound should be not played (different area)
        text_to_speech.assert_called_once()
        assert text_to_speech.call_args.kwargs.get("override_media_path") is None
        assert len(turn_on) == 1

        # Restore
        light_2 = entity_registry.async_update_entity(
            light_2.entity_id, area_id=area_1.id
        )

        # 3. Remove satellite device area
        entity_registry.async_update_entity(satellite.entity_id, area_id=None)
        device_registry.async_update_device(satellite_device.id, area_id=None)

        _reset()
        await _run("turn on light 1")

        # Acknowledgment sound should be not played (no satellite area)
        text_to_speech.assert_called_once()
        assert text_to_speech.call_args.kwargs.get("override_media_path") is None
        assert len(turn_on) == 1

        # Restore
        entity_registry.async_update_entity(satellite.entity_id, area_id=area_1.id)
        device_registry.async_update_device(satellite_device.id, area_id=area_1.id)

        # 4. Check device area instead of entity area
        light_device = device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            connections=set(),
            identifiers={("demo", "id-5678")},
        )
        device_registry.async_update_device(light_device.id, area_id=area_1.id)
        light_2 = entity_registry.async_update_entity(
            light_2.entity_id, area_id=None, device_id=light_device.id
        )

        _reset()
        await _run("turn on the lights")

        # Acknowledgment sound should be played (same area)
        text_to_speech.assert_called_once()
        assert (
            text_to_speech.call_args.kwargs["override_media_path"] == ACKNOWLEDGE_PATH
        )
        assert len(turn_on) == 2

        # 5. Move device to different area
        device_registry.async_update_device(light_device.id, area_id=area_2.id)

        _reset()
        await _run("turn on light 2")

        # Acknowledgment sound should be not played (different device area)
        text_to_speech.assert_called_once()
        assert text_to_speech.call_args.kwargs.get("override_media_path") is None
        assert len(turn_on) == 1

        # 6. No device or area
        light_2 = entity_registry.async_update_entity(
            light_2.entity_id, area_id=None, device_id=None
        )

        _reset()
        await _run("turn on light 2")

        # Acknowledgment sound should be not played (no area)
        text_to_speech.assert_called_once()
        assert text_to_speech.call_args.kwargs.get("override_media_path") is None
        assert len(turn_on) == 1

        # 7. Not in entity registry
        hass.states.async_set("light.light_3", "off", {ATTR_FRIENDLY_NAME: "light 3"})

        _reset()
        await _run("turn on light 3")

        # Acknowledgment sound should be not played (not in entity registry)
        text_to_speech.assert_called_once()
        assert text_to_speech.call_args.kwargs.get("override_media_path") is None
        assert len(turn_on) == 1

    # Check TTS event
    events.clear()
    await _run("turn on light 1")

    has_acknowledge_override: bool | None = None
    for event in events:
        if event.type == PipelineEventType.TTS_START:
            assert event.data
            has_acknowledge_override = event.data["acknowledge_override"]
            break

    assert has_acknowledge_override