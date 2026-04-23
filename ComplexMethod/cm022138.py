async def test_context_user_ids_lru_eviction(
    hass: HomeAssistant,
) -> None:
    """Test that the parent context user-id cache is bounded by LRU eviction.

    The cache must keep memory bounded under sustained load. New entries
    arriving after the cap evict the least recently used entries. An
    early parent context whose entry has been evicted should no longer
    contribute its user_id to a later child state change.
    """
    user_id = "b400facee45711eaa9308bfd3d19e474"
    early_parent_context = ha.Context(
        id="01GTDGKBCH00GW0X476W5TVAAA",
        user_id=user_id,
    )
    child_context = ha.Context(
        id="01GTDGKBCH00GW0X476W5TVDDD",
        parent_id=early_parent_context.id,
    )

    logbook_run = logbook.processor.LogbookRun(
        context_lookup={None: None},
        external_events={},
        event_cache=logbook.processor.EventCache({}),
        entity_name_cache=logbook.processor.EntityNameCache(hass),
        include_entity_name=True,
        timestamp=False,
        memoize_new_contexts=False,
        for_live_stream=True,
    )
    context_augmenter = logbook.processor.ContextAugmenter(logbook_run)
    ent_reg = er.async_get(hass)

    processor = logbook.processor.EventProcessor.__new__(
        logbook.processor.EventProcessor
    )
    processor.hass = hass
    processor.ent_reg = ent_reg
    processor.logbook_run = logbook_run
    processor.context_augmenter = context_augmenter

    hass.states.async_set("switch.heater", STATE_OFF)
    await hass.async_block_till_done()

    # Seed: the early parent SERVICE_CALL event populates the cache.
    parent_row = MockRow(
        EVENT_CALL_SERVICE,
        {
            ATTR_DOMAIN: "climate",
            ATTR_SERVICE: "set_hvac_mode",
            "service_data": {ATTR_ENTITY_ID: "climate.living_room"},
        },
        context=early_parent_context,
    )
    parent_row.context_only = True
    parent_row.icon = None
    processor.humanify([parent_row])
    assert (
        ulid_to_bytes_or_none(early_parent_context.id) in logbook_run.context_user_ids
    )

    # Flood the cache with MAX+1 unrelated parent contexts so the early
    # parent is evicted from the front of the LRU.
    filler_rows = []
    for index in range(logbook.processor.MAX_CONTEXT_USER_IDS_CACHE + 1):
        filler_context = ha.Context(
            user_id=f"ffffffff{index:024x}"[:32],
        )
        filler_row = MockRow(
            EVENT_CALL_SERVICE,
            {
                ATTR_DOMAIN: "test",
                ATTR_SERVICE: "noop",
                "service_data": {},
            },
            context=filler_context,
        )
        filler_row.context_only = True
        filler_row.icon = None
        filler_rows.append(filler_row)
    processor.humanify(filler_rows)

    assert (
        len(logbook_run.context_user_ids)
        == logbook.processor.MAX_CONTEXT_USER_IDS_CACHE
    )
    assert (
        ulid_to_bytes_or_none(early_parent_context.id)
        not in logbook_run.context_user_ids
    )

    # The child state change can no longer inherit the early parent's user_id
    # because that entry was evicted.
    child_row = MockRow(
        PSEUDO_EVENT_STATE_CHANGED,
        context=child_context,
    )
    child_row.state = STATE_ON
    child_row.entity_id = "switch.heater"
    child_row.icon = None
    results = processor.humanify([child_row])

    heater_entries = [e for e in results if e.get("entity_id") == "switch.heater"]
    assert len(heater_entries) == 1
    assert "context_user_id" not in heater_entries[0]