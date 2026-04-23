def _get_commodity_countries(commodity_code: str) -> dict[str, str]:
    """Fetch valid country names for a commodity using the metadata API.

    Parameters
    ----------
    commodity_code : str
        Commodity code (e.g., '0440000' for corn)

    Returns
    -------
    dict[str, str]
        Mapping of country name -> country code
    """
    # pylint: disable=import-outside-toplevel
    from openbb_core.provider.utils.helpers import make_request

    base_url = "https://apps.fas.usda.gov/PSDOnlineApi/api/CompositeVisualization/GetCountries?regionCode=R00&commodityCode="

    try:
        resp = make_request(
            f"{base_url}{commodity_code}",
        )
        if resp.status_code == 200:
            data = resp.json()
            name_to_code = {}
            for item in data:
                code = item.get("value")
                name = item.get("text", "").strip()
                if code and name and code != "00":  # Skip "All Countries" (00)
                    name_to_code[name] = code
            if name_to_code:
                return name_to_code
    except Exception:  # noqa  # pylint: disable=broad-except
        pass
    # Fallback: return empty (will use global COUNTRIES list)
    return {}