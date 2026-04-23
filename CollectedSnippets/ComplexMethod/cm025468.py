async def async_setup_entry(
    hass: HomeAssistant,
    entry: FluxLedConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Flux lights."""
    coordinator = entry.runtime_data
    device = coordinator.device
    entities: list[
        FluxSpeedNumber
        | FluxPixelsPerSegmentNumber
        | FluxSegmentsNumber
        | FluxMusicPixelsPerSegmentNumber
        | FluxMusicSegmentsNumber
    ] = []
    base_unique_id = entry.unique_id or entry.entry_id

    if device.pixels_per_segment is not None:
        entities.append(
            FluxPixelsPerSegmentNumber(
                coordinator,
                base_unique_id,
                "pixels_per_segment",
            )
        )
    if device.segments is not None:
        entities.append(FluxSegmentsNumber(coordinator, base_unique_id, "segments"))
    if device.music_pixels_per_segment is not None:
        entities.append(
            FluxMusicPixelsPerSegmentNumber(
                coordinator,
                base_unique_id,
                "music_pixels_per_segment",
            )
        )
    if device.music_segments is not None:
        entities.append(
            FluxMusicSegmentsNumber(coordinator, base_unique_id, "music_segments")
        )
    if device.effect_list and device.effect_list != [EFFECT_RANDOM]:
        entities.append(FluxSpeedNumber(coordinator, base_unique_id, None))

    async_add_entities(entities)