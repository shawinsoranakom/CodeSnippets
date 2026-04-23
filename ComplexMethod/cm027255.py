def seen_all_fields(
    previous_match: IntegrationMatchHistory,
    advertisement_data: AdvertisementData,
    name: str,
) -> bool:
    """Return if we have seen all fields."""
    if previous_match.name != name:
        return False
    if not previous_match.manufacturer_data and advertisement_data.manufacturer_data:
        return False
    if advertisement_data.service_data and (
        not previous_match.service_data
        or not previous_match.service_data.issuperset(advertisement_data.service_data)
    ):
        return False
    if advertisement_data.service_uuids and (
        not previous_match.service_uuids
        or not previous_match.service_uuids.issuperset(advertisement_data.service_uuids)
    ):
        return False
    return True