def check_missing_country_data(
    df: "pd.DataFrame",
    requested_countries: list[str],
    dates: list[Any],
    countries: list[str],
) -> None:
    """Check which requested countries have no data for selected dates and warn.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame containing IMF indicator data.
    requested_countries : list[str]
        List of country codes/names requested by the user.
    dates : list[Any]
        List of dates in the selected date range.
    countries : list[str]
        List of countries that have data.
    """
    # pylint: disable=import-outside-toplevel
    from openbb_core.app.model.abstract.warning import OpenBBWarning

    # Build a set of countries that have data for the selected dates
    countries_with_data_for_dates: set[str] = set()
    for d in dates:
        date_df = df[df["date"] == d]
        countries_with_data_for_dates.update(date_df["country"].dropna().unique())

    # Check each requested country
    missing_countries: list[tuple[str, Any]] = []
    for req_country in requested_countries:
        # Find the actual country name (we have codes like DEU, USA)
        # Check if any country in data matches this code
        for c in countries:
            if c and (
                req_country.upper() in c.upper()
                or df[df["country"] == c]["country_code"].iloc[0] == req_country.upper()
            ):
                if c not in countries_with_data_for_dates:
                    # Get the latest date this country has data for
                    country_dates = sorted(
                        df[df["country"] == c]["date"].dropna().unique(),
                        reverse=True,
                    )
                    latest = country_dates[0] if country_dates else None
                    missing_countries.append((c, latest))
                break

    if missing_countries:
        for country_name, latest_date in missing_countries:
            warnings.warn(
                f"No data for '{country_name}' in selected date range. "
                f"Latest available data: {latest_date}. "
                f"Try increasing 'limit' or adjusting date range.",
                OpenBBWarning,
            )