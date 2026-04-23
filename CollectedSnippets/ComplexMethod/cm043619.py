async def aextract_data(
        query: FREDCommercialPaperParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Extract data."""
        ids: list[str] = []
        if query.maturity == "all" and query.category == "all":
            ids = ALL_IDS
        else:
            MAT_DICT = {
                "overnight": "01",
                "7d": "07",
                "15d": "15",
                "30d": "30",
                "60d": "60",
                "90d": "90",
            }
            CAT_DICT = {
                "asset_backed": "AAAD",
                "financial": "FAAD",
                "nonfinancial": "NAAD",
                "a2p2": "NA2P2D",
            }
            maturities = query.maturity.split(",")
            categories = query.category.split(",")
            if "all" in categories:
                categories = list(CAT_DICT)
            if "all" in maturities:
                maturities = list(MAT_DICT)
            for cat in categories:
                for mat in maturities:
                    ids.append(f"RIFSPP{CAT_DICT.get(cat)}{MAT_DICT.get(mat)}NB")
        try:
            response = await FredSeriesFetcher.fetch_data(
                dict(
                    symbol=",".join(ids),
                    start_date=query.start_date if query.start_date else "2019-01-01",
                    end_date=query.end_date,
                    frequency=query.frequency,
                    aggregation_method=query.aggregation_method,
                    transform=query.transform,
                ),
                credentials,
            )
        except Exception as e:
            raise e from e

        return {
            "metadata": response.metadata,
            "data": [d.model_dump() for d in response.result],
        }