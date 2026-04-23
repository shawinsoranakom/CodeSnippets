async def parse_form_4_data(  # noqa: PLR0915, PLR0912  # pylint: disable=too-many-branches
    data,
):
    """Parse the Form 4 data."""

    owner = data.get("reportingOwner", {})
    owners = ""
    ciks = ""
    if isinstance(owner, list):
        owners = ";".join(
            [d.get("reportingOwnerId", {}).get("rptOwnerName") for d in owner]
        )
        ciks = ";".join(
            [d.get("reportingOwnerId", {}).get("rptOwnerCik") for d in owner]
        )

    issuer = data.get("issuer", {})
    owner_relationship = (
        owner.get("reportingOwnerRelationship", {})
        if isinstance(owner, dict)
        else (
            owner[0].get("reportingOwnerRelationship", {})
            if isinstance(owner, list)
            else {}
        )
    )
    signature_data = data.get("ownerSignature")

    if signature_data and isinstance(signature_data, dict):
        signature_date = signature_data.get("signatureDate")
    elif signature_data and isinstance(signature_data, list):
        signature_date = signature_data[0].get("signatureDate")
    else:
        signature_date = None

    footnotes = data.get("footnotes", {})
    if footnotes:
        footnote_items = footnotes.get("footnote")
        if isinstance(footnote_items, dict):
            footnote_items = [footnote_items]
        footnotes = {item["@id"]: item["#text"] for item in footnote_items}

    metadata = {
        "filing_date": signature_date or data.get("periodOfReport"),
        "symbol": issuer.get("issuerTradingSymbol", "").upper(),
        "form": data.get("documentType"),
        "owner": (
            owners if owners else owner.get("reportingOwnerId", {}).get("rptOwnerName")  # type: ignore
        ),
        "owner_cik": (
            ciks if ciks else owner.get("reportingOwnerId", {}).get("rptOwnerCik")  # type: ignore
        ),
        "issuer": issuer.get("issuerName"),
        "issuer_cik": issuer.get("issuerCik"),
        **owner_relationship,
    }
    results: list = []

    if data.get("nonDerivativeTable") and (
        data["nonDerivativeTable"].get("nonDerivativeTransaction")
        or data["nonDerivativeTable"].get("nonDerivativeHolding")
    ):
        temp_table = data["nonDerivativeTable"]
        tables = (
            temp_table["nonDerivativeTransaction"]
            if temp_table.get("nonDerivativeTransaction")
            else temp_table["nonDerivativeHolding"]
        )
        parsed_table1: list = []
        if isinstance(tables, dict):
            tables = [tables]
        for table in tables:
            if isinstance(table, str):
                continue
            new_row = {**metadata}
            for key, value in table.items():
                if key == "transactionCoding":
                    new_row["transaction_type"] = value.get("transactionCode")
                    new_row["form"] = (
                        value.get("transactionFormType") or metadata["form"]
                    )
                elif isinstance(value, dict):
                    if "footnoteId" in value:
                        if isinstance(value["footnoteId"], list):
                            ids = [item["@id"] for item in value["footnoteId"]]
                            footnotes = (
                                "; ".join(
                                    [
                                        footnotes.get(footnote_id, "")
                                        for footnote_id in ids
                                    ]
                                )
                                if isinstance(footnotes, dict)
                                else footnotes
                            )
                            new_row["footnote"] = footnotes
                        else:
                            footnote_id = value["footnoteId"]["@id"]
                            new_row["footnote"] = (
                                (
                                    footnotes
                                    if isinstance(footnotes, str)
                                    else footnotes.get(footnote_id)
                                )
                                if footnotes
                                else None
                            )
                    for k, v in value.items():
                        if k == "value":
                            new_row[key] = v
                        if isinstance(v, dict):
                            if "footnoteId" in v:
                                if isinstance(v["footnoteId"], list):
                                    ids = [item["@id"] for item in v["footnoteId"]]
                                    footnotes = (
                                        footnotes
                                        if isinstance(footnotes, str)
                                        else (
                                            "; ".join(
                                                [
                                                    footnotes.get(footnote_id, "")
                                                    for footnote_id in ids
                                                ]
                                            )
                                            if footnotes
                                            else None
                                        )
                                    )
                                    new_row["footnote"] = footnotes
                                else:
                                    footnote_id = v["footnoteId"]["@id"]
                                    new_row["footnote"] = (
                                        (
                                            footnotes
                                            if isinstance(footnotes, str)
                                            else footnotes.get(footnote_id)
                                        )
                                        if footnotes
                                        else None
                                    )
                            for k1, v1 in v.items():
                                if k1 == "value":
                                    new_row[k] = v1
            if new_row:
                parsed_table1.append(new_row)

        results.extend(parsed_table1)

    if (
        data.get("derivativeTable")
        and data["derivativeTable"].get("derivativeTransaction")
    ) or data.get("derivativeSecurity"):
        parsed_table2: list = []
        tables = (
            data["derivativeSecurity"]
            if data.get("derivativeSecurity")
            else data["derivativeTable"]["derivativeTransaction"]
        )
        if isinstance(tables, dict):
            tables = [tables]
        for table in tables:
            if isinstance(table, str):
                continue
            new_row = {**metadata}
            for key, value in table.items():
                if key == "transactionCoding":
                    new_row["transaction_type"] = value.get("transactionCode")
                    new_row["form"] = (
                        value.get("transactionFormType") or metadata["form"]
                    )
                elif isinstance(value, dict):
                    for k, v in value.items():
                        if k == "value":
                            new_row[key] = v
                        if isinstance(v, dict):
                            for k1, v1 in v.items():
                                if k1 == "value":
                                    new_row[k] = v1
            t_value = new_row.pop("transactionValue", None)
            if t_value:
                new_row["transactionTotalValue"] = t_value
            parsed_table2.append(new_row)

        results.extend(parsed_table2)

    return results