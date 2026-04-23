async def get_factor_choices(
    region: str | None = None,
    factor: str | None = None,
    is_portfolio: bool = False,
    portfolio: str | None = None,
):
    """Get the list of choices for factors based on combinations of parameters.

    This function is for generating choices for Workspace dropdown menus.
    It is not intended to be used directly.

    Parameters
    ----------
    region : Optional[str]
        The region for which to get factor choices. If None, all regions are considered.
    factor : Optional[str]
        The specific factor for which to get choices. If None, all factors for the region are
        considered.
    is_portfolio : bool
        If True, the function will return portfolio choices instead of factor choices.
    portfolio : Optional[str]
        A specific portfolio.

    Returns
    -------
    list
        A list of dictionaries representing the choices for factors or portfolios.
        Each dictionary contains a 'label' and a 'value' key.
    """
    if region and not factor and not is_portfolio:
        factors = FACTOR_REGION_MAP.get(region, {}).get("factors", {})
        return [
            {
                "label": k.replace("_", " ")
                .title()
                .replace("Lt", "LT")
                .replace("St", "ST"),
                "value": k,
            }
            for k in list(factors)
        ]
    if region and factor and not is_portfolio:
        intervals = (
            FACTOR_REGION_MAP.get(region, {}).get("intervals", {}).get(factor, {})
        )
        intervals = [
            {"label": k.replace("_", " ").title(), "value": k} for k in list(intervals)
        ]
        return intervals

    if not is_portfolio:
        return [
            {"label": k.replace("_", " ").title(), "value": k}
            for k in list(FACTOR_REGION_MAP)
        ]
    region = region or ""
    mapped_region = REGIONS_MAP.get(region, "").replace("_", " ")
    if is_portfolio and region and not portfolio:
        portfolios = (
            [
                {
                    "label": (
                        d["label"].replace(mapped_region, "").strip()
                        if region != "america"
                        else d["label"]
                    ),
                    "value": d["value"],
                }
                for d in DATASET_CHOICES
                if "Portfolio" in d.get("value", "")
                and d["value"].startswith(REGIONS_MAP.get(region, region))
                and "daily" not in d.get("value", "").lower()
            ]
            if region != "america"
            else [
                d
                for d in DATASET_CHOICES
                if "Portfolio" in d.get("value", "")
                and all(
                    not d.get("value", "").startswith(reg)
                    for reg in REGIONS_MAP.values()
                    if reg
                )
                and "daily" not in d.get("value", "").lower()
            ]
        )

        if "ex_" not in region:
            portfolios = [d for d in portfolios if "ex_" not in d.get("value", "")]

        return portfolios

    if is_portfolio and region and portfolio:
        portfolios = (
            [
                d
                for d in DATASET_CHOICES
                if "Portfolio" in d.get("value", "")
                and d["value"].startswith(REGIONS_MAP.get(region, region))
                and portfolio in d.get("value", "")
            ]
            if region != "america"
            else [
                d
                for d in DATASET_CHOICES
                if "Portfolio" in d.get("value", "")
                and all(
                    not d.get("value", "").startswith(reg)
                    for reg in REGIONS_MAP.values()
                    if reg
                )
                and portfolio in d.get("value", "")
            ]
        )
        has_daily = False
        frequencies = ["monthly", "annual"]

        for d in portfolios:
            if "daily" in d.get("value", "").lower():
                has_daily = True
                break

        frequencies = ["daily"] + frequencies if has_daily else frequencies

        return [{"label": k.title(), "value": k} for k in frequencies]

    return [{"label": "No choices found. Try a new parameter.", "value": None}]