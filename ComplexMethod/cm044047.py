def _get_commodity_attributes(commodity_code: str) -> list[str]:
    """Fetch valid attribute names for a commodity using the metadata API."""
    # pylint: disable=import-outside-toplevel
    from openbb_core.provider.utils.helpers import make_request

    try:
        resp = make_request(
            f"https://apps.fas.usda.gov/PSDOnlineApi/api/query/GetMultiCommodityAttributes?commodityCodes={commodity_code},"
        )
        if resp.status_code == 200:
            data = resp.json()
            id_to_key = {v: k for k, v in ATTRIBUTES.items()}
            valid_keys = set()

            for item in data:
                attr_id = item.get("attributeId")
                if attr_id and attr_id in id_to_key:
                    valid_keys.add(id_to_key[attr_id])
            if valid_keys:
                return sorted(list(valid_keys))
    except Exception:  # noqa  # pylint: disable=broad-except
        pass
    # Fallback: return all attributes
    return list(ATTRIBUTES.keys())