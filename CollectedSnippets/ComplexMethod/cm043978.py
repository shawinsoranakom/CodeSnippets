def transform_data(
        query: FMPForwardEbitdaEstimatesQueryParams, data: list, **kwargs: Any
    ) -> list[FMPForwardEbitdaEstimatesData]:
        """Return the transformed data."""
        symbols = query.symbol.split(",") if query.symbol else []
        cols = [
            "symbol",
            "date",
            "ebitdaAvg",
            "ebitdaHigh",
            "ebitdaLow",
        ]
        year = datetime.now().year
        results: list[FMPForwardEbitdaEstimatesData] = []
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
            results.append(FMPForwardEbitdaEstimatesData.model_validate(temp))

        return results