def _fill_missing(cls, values):
        """Fill missing information that can be identified."""
        description = values.get("assetDescription", "").lower()
        if not values.get("owner"):
            values["owner"] = "Self"
        if (values.get("ticker") or values.get("symbol")) and not values.get(
            "assetType"
        ):
            values["asset_type"] = "ETF" if "etf" in description else "Stock"
        elif (
            not values.get("ticker")
            and not values.get("symbol")
            and not values.get("assetType")
        ):
            values["asset_type"] = (
                "Treasury"
                if "treasury" in description or "bill" in description
                else (
                    "Bond"
                    if "%" in description
                    or "due" in description
                    or "pct" in description
                    else (
                        "Fund"
                        if "fund" in description
                        else ("ETF" if "etf" in description else None)
                    )
                )
            )
        return values