def process_projections(data: dict) -> list[dict]:
    """Process projection data."""
    # Get dates first
    dates = []
    for key, value in data.items():
        dates.extend([entry["date"] for entry in value])
    full_dates = sorted(list(set(dates)))

    # Loop through date and get dictionary of all keys
    ldata = []
    for date in full_dates:
        entry = {"date": date}
        for key, value in data.items():
            val = [item["value"] for item in value if item["date"] == date]
            if val:
                entry[key] = float(val[0]) if val[0] != "." else None
            else:
                entry[key] = None
        ldata.append(entry)

    return ldata