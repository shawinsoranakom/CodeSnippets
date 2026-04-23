def create_mock_zone_from_dict(
    zone_data: dict[str, Any],
) -> AsyncMock:
    """Create a mock TotalConnectZone from a dictionary."""
    return create_mock_zone(
        zone_data["ZoneID"],
        zone_data["PartitionId"],
        zone_data["ZoneDescription"],
        ZoneStatus(zone_data["ZoneStatus"]),
        zone_data["ZoneTypeId"],
        zone_data["CanBeBypassed"],
        zone_data.get("Batterylevel"),
        zone_data.get("Signalstrength"),
        (zone_data["zoneAdditionalInfo"] or {}).get("SensorSerialNumber"),
        (zone_data["zoneAdditionalInfo"] or {}).get("LoopNumber"),
        (zone_data["zoneAdditionalInfo"] or {}).get("ResponseType"),
        (zone_data["zoneAdditionalInfo"] or {}).get("AlarmReportState"),
        (zone_data["zoneAdditionalInfo"] or {}).get("ZoneSupervisionType"),
        (zone_data["zoneAdditionalInfo"] or {}).get("ChimeState"),
        (zone_data["zoneAdditionalInfo"] or {}).get("DeviceType"),
    )