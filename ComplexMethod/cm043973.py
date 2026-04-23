def transform_data(
        query: FMPCurrencySnapshotsQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[FMPCurrencySnapshotsData]:
        """Filter by the query parameters and validate the model."""
        # pylint: disable=import-outside-toplevel
        from datetime import timezone  # noqa
        from numpy import nan
        from pandas import DataFrame, concat
        from openbb_core.provider.utils.helpers import safe_fromtimestamp

        if not data:
            raise EmptyDataError("No data was returned from the FMP endpoint.")

        # Drop all the zombie columns FMP returns.
        df = DataFrame(data).dropna(how="all", axis=1).drop(columns=["exchange"])

        new_df = DataFrame()

        # Filter for the base currencies requested and the quote_type.
        for symbol in query.base.split(","):
            temp = (
                df.query("`symbol`.str.startswith(@symbol)")
                if query.quote_type == "indirect"
                else df.query("`symbol`.str.endswith(@symbol)")
            ).rename(columns={"symbol": "base_currency", "name": "counter_currency"})
            temp["base_currency"] = symbol
            temp["counter_currency"] = (
                [d.split("/")[1] for d in temp["counter_currency"]]
                if query.quote_type == "indirect"
                else [d.split("/")[0] for d in temp["counter_currency"]]
            )
            # Filter for the counter currencies, if requested.
            if query.counter_currencies is not None:
                counter_currencies = (  # noqa: F841  # pylint: disable=unused-variable
                    query.counter_currencies
                    if isinstance(query.counter_currencies, list)
                    else query.counter_currencies.split(",")
                )
                temp = (
                    temp.query("`counter_currency`.isin(@counter_currencies)")
                    .set_index("counter_currency")
                    # Sets the counter currencies in the order they were requested.
                    .filter(items=counter_currencies, axis=0)
                    .reset_index()
                ).rename(columns={"index": "counter_currency"})
            # If there are no records, don't concatenate.
            if len(temp) > 0:
                # Convert the Unix timestamp to a datetime.
                temp.timestamp = temp.timestamp.apply(
                    lambda x: safe_fromtimestamp(x, tz=timezone.utc)
                )
                new_df = concat([new_df, temp])
            if len(new_df) == 0:
                raise EmptyDataError(
                    "No data was found using the applied filters. Check the parameters."
                )
            new_df = new_df.replace({nan: None})

        return [
            FMPCurrencySnapshotsData.model_validate(d)
            for d in new_df.reset_index(drop=True).to_dict(orient="records")
        ]