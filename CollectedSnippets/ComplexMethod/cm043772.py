async def parse_13f_hr(filing: str):
    """Parse a 13F-HR filing from the Complete Submission TXT file string."""
    # pylint: disable=import-outside-toplevel
    import xmltodict
    from bs4 import BeautifulSoup
    from numpy import nan
    from pandas import DataFrame, to_datetime

    # Check if the input string is a URL
    if filing.startswith("https://"):
        filing = await get_complete_submission(filing)  # type: ignore

    soup = BeautifulSoup(filing, "xml")

    info_table = soup.find_all("informationTable")

    if not info_table:
        info_table = soup.find_all("table")[-1]  # type: ignore[assignment]

    parsed_xml = xmltodict.parse(
        str(info_table[0]).replace("ns1:", "").replace("n1:", "")  # type: ignore
    )["informationTable"]["infoTable"]

    if parsed_xml is None:
        raise OpenBBError(
            "Failed to parse the 13F-HR information table."
            + " Check the `filing_str` to make sure it is valid and contains the tag 'informationTable'."
            + " Documents filed before Q2 2013 are not supported."
        )

    period_ending = get_period_ending(soup)  # type: ignore
    data = (
        DataFrame(parsed_xml)
        if isinstance(parsed_xml, list)
        else DataFrame([parsed_xml])
    )
    data.columns = data.columns.str.replace("ns1:", "")
    data["value"] = data["value"].astype(int)
    security_type: list = []
    principal_amount: list = []

    # Unpack the nested objects
    try:
        security_type = [d.get("sshPrnamtType") for d in data["shrsOrPrnAmt"]]
        data["security_type"] = security_type
        principal_amount = [int(d.get("sshPrnamt", 0)) for d in data["shrsOrPrnAmt"]]
        data["principal_amount"] = principal_amount
        _ = data.pop("shrsOrPrnAmt")
    except ValueError:
        pass
    try:
        sole = [d.get("Sole") for d in data["votingAuthority"]]
        shared = [d.get("Shared") for d in data["votingAuthority"]]
        none = [d.get("None") for d in data["votingAuthority"]]
        data["voting_authority_sole"] = [int(s) if s else 0 for s in sole]
        data["voting_authority_shared"] = [int(s) if s else 0 for s in shared]
        data["voting_authority_none"] = [int(s) if s else 0 for s in none]
        _ = data.pop("votingAuthority")
    except ValueError:
        pass

    if "putCall" in data.columns:
        data["putCall"] = data["putCall"].fillna("--")

    # Add the period ending so that the filing is identified when multiple are requested.
    data["period_ending"] = to_datetime(period_ending, yearfirst=False).date()
    df = DataFrame(data)
    # Aggregate the data because there are multiple entries for each security and we need the totals.
    # We break it down by CUSIP, security type, and option type.
    agg_index = [
        "period_ending",
        "nameOfIssuer",
        "cusip",
        "titleOfClass",
        "security_type",
        "putCall",
        "investmentDiscretion",
    ]
    agg_columns = {
        "value": "sum",
        "principal_amount": "sum",
        "voting_authority_sole": "sum",
        "voting_authority_shared": "sum",
        "voting_authority_none": "sum",
    }
    # Only aggregate columns that exist in the DataFrame
    agg_columns = {k: v for k, v in agg_columns.items() if k in df.columns}
    agg_index = [k for k in agg_index if k in df.columns]
    df = df.groupby([*agg_index]).agg(agg_columns)

    for col in [
        "voting_authority_sole",
        "voting_authority_shared",
        "voting_authority_none",
    ]:
        if col in df.columns and all(df[col] == 0):
            df.drop(columns=col, inplace=True)

    total_value = df.value.sum()
    df["weight"] = round(df.value.astype(float) / total_value, 6)

    return (
        df.reset_index()
        .replace({nan: None, "--": None})
        .sort_values(by="weight", ascending=False)
        .to_dict("records")
    )