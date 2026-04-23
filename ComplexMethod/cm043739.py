async def aextract_data(
        query: SecForm13FHRQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw data from the SEC endpoint."""
        # pylint: disable=import-outside-toplevel
        import asyncio  # noqa
        from openbb_core.app.model.abstract.error import OpenBBError
        from openbb_core.provider.utils.errors import EmptyDataError
        from openbb_sec.utils import parse_13f

        symbol = query.symbol
        urls: list = []
        cik = symbol.isnumeric()
        try:
            filings = (
                await parse_13f.get_13f_candidates(symbol=symbol)
                if cik is False
                else await parse_13f.get_13f_candidates(cik=symbol)
            )
            if query.limit and query.date is None:
                urls = filings.iloc[: query.limit].to_list()
            if query.date is not None:
                date = parse_13f.date_to_quarter_end(query.date.strftime("%Y-%m-%d"))
                filings.index = filings.index.astype(str)
                urls = [filings.loc[date]]

            results: list = []

            async def get_filing(url):
                """Get a single 13F-HR filing and parse it."""
                data = await parse_13f.parse_13f_hr(url)

                if len(data) > 0:
                    results.extend(data)

            await asyncio.gather(*[get_filing(url) for url in urls])

            if not results:
                raise EmptyDataError("No data was returned with the given parameters.")

            return results
        except OpenBBError as e:
            raise e from e