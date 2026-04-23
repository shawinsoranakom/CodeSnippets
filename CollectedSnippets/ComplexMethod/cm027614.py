def _add_areas(
    areas: ar.AreaRegistry,
    devices: dr.DeviceRegistry,
    candidates: Iterable[MatchTargetsCandidate],
) -> None:
    """Add area and device entries to match candidates."""
    for candidate in candidates:
        if candidate.entity is None:
            continue

        if candidate.entity.device_id:
            candidate.device = devices.async_get(candidate.entity.device_id)

        if candidate.entity.area_id:
            # Use entity area first
            candidate.area = areas.async_get_area(candidate.entity.area_id)
            assert candidate.area is not None
        elif (candidate.device is not None) and candidate.device.area_id:
            # Fall back to device area
            candidate.area = areas.async_get_area(candidate.device.area_id)