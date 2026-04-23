async def aextract_data(
        query: FMPEarningsCallTranscriptQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw data from the FMP endpoint."""
        # pylint: disable=import-outside-toplevel
        import warnings  # noqa
        from openbb_fmp.utils.helpers import (
            get_available_transcript_symbols,
            get_data_one,
            get_transcript_dates_for_symbol,
        )
        from pandas import DataFrame

        api_key = credentials.get("fmp_api_key") if credentials else ""

        available_symbols = get_available_transcript_symbols(api_key=api_key)
        avail_df = DataFrame(available_symbols)

        if query.symbol.upper() not in avail_df["symbol"].values:
            raise OpenBBError(
                ValueError(
                    f"Symbol {query.symbol} not found in available transcripts."
                    + f"\n Available symbols include: {', '.join(sorted(avail_df['symbol'].unique().tolist()))}"
                )
            )
        symbol_transcripts = get_transcript_dates_for_symbol(
            query.symbol.upper(), api_key=api_key
        )

        df_dates = DataFrame(symbol_transcripts).sort_values(by="date", ascending=False)
        year = df_dates.iloc[0].fiscalYear

        if query.year and query.year not in df_dates.fiscalYear.values:
            warnings.warn(
                f"Year {query.year} not found in available transcripts for {query.symbol}."
                + f" Using latest year {year} instead."
            )

        year = query.year if query.year in df_dates.fiscalYear.values else year

        quarter = query.quarter if query.quarter else df_dates.iloc[0].quarter

        if (
            query.quarter
            and query.quarter
            not in df_dates.query("fiscalYear == @year").quarter.values
        ):
            warnings.warn(
                f"Quarter {query.quarter} not found in available transcripts for {query.symbol} in {year}."
                + f" Using latest quarter q{df_dates.query('fiscalYear == @year').iloc[0].quarter} instead."
            )

        url = (
            "https://financialmodelingprep.com/stable/earning-call-transcript?symbol="
            + f"{query.symbol.upper()}&year={year}&quarter={quarter}&apikey={api_key}"
        )

        try:
            return await get_data_one(url, **kwargs)
        except ValueError as e:
            raise OpenBBError(
                f"No transcript found for {query.symbol} in {year} Q{quarter}"
                f". \n Latest available transcript is {df_dates.iloc[0].fiscalYear} Q{df_dates.iloc[0].quarter}."
            ) from e