async def fetch_all_pages(
            start_date: str,
            end_date: str = "",
            rid: str = "",
        ) -> DataFrame:
            """Fetch all pages of the FRED releases calendar for each date in a range.

            If a release ID is supplied, the entire date range is fetched in a single
            paginated call. Otherwise, each date is fetched individually to ensure
            complete results.
            """
            end_date = end_date or start_date

            if rid:
                # A specific release ID can be fetched across the full range at once.
                return await fetch_date_pages(start_date, end_date, rid)

            # Without a release ID, fetch each date individually.
            dates = [
                d.strftime("%Y-%m-%d") for d in pd_date_range(start_date, end_date)
            ]

            results = await asyncio.gather(*[fetch_date_pages(d) for d in dates])

            frames = [r for r in results if not r.empty]

            if not frames:
                return DataFrame()

            return concat(frames, ignore_index=True).sort_values(by="date")