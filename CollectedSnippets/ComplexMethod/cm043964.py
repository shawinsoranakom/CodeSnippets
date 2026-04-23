def transform_data(
        query: FMPForwardEpsEstimatesQueryParams, data: list[dict], **kwargs: Any
    ) -> list[FMPForwardEpsEstimatesData]:
        """Return the transformed data."""
        symbols = query.symbol.split(",") if query.symbol else []
        cols = [
            "symbol",
            "date",
            "epsAvg",
            "epsHigh",
            "epsLow",
            "numberAnalystsEps",
        ]
        year = datetime.now().year
        results: list[FMPForwardEpsEstimatesData] = []

        for item in sorted(
            data,
            key=lambda item: (  # type: ignore
                (
                    symbols.index(item.get("symbol")) if item.get("symbol") in symbols else len(symbols),  # type: ignore
                    item.get("date"),
                )
                if symbols
                else item.get("date")
            ),
        ):
            temp: dict[str, Any] = {}

            for col in cols:
                temp[col] = item.get(col)

            if (
                query.include_historical is False
                and datetime.strptime(temp["date"], "%Y-%m-%d").year < year
            ):
                continue

            results.append(FMPForwardEpsEstimatesData.model_validate(temp))

        return results