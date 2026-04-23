async def aextract_data(
        query: SecManagementDiscussionAnalysisQueryParams,
        credentials: dict[str, Any] | None,
        **kwargs: Any,
    ) -> dict:  # type: ignore[override]
        """Extract the data."""
        # pylint: disable=import-outside-toplevel
        import re

        from aiohttp_client_cache import SQLiteBackend
        from aiohttp_client_cache.session import CachedSession
        from openbb_core.app.utils import get_user_cache_directory
        from openbb_core.provider.utils.helpers import amake_request
        from openbb_sec.models.company_filings import SecCompanyFilingsFetcher
        from openbb_sec.utils.helpers import SEC_HEADERS, sec_callback
        from pandas import offsets, to_datetime

        def _extract_exhibit_links(
            index_html: str, type_prefix: str = "EX-99"
        ) -> list[str]:
            """Parse a filing index page and return hrefs for rows
            whose Type cell starts with *type_prefix* (e.g. ``EX-99``).

            The SEC filing-index table has columns:
            Seq | Description | Document (with <a href>) | Type | Size
            The TYPE label (e.g. ``EX-99.1``) lives in the cell text,
            *not* in the href URL, so we must parse the table rows.
            """
            _row_re = re.compile(r"<tr[^>]*>(.*?)</tr>", re.I | re.S)
            results: list[str] = []
            for rm in _row_re.finditer(index_html):
                cells = re.findall(r"<td[^>]*>(.*?)</td>", rm.group(1), re.I | re.S)
                if len(cells) < 4:
                    continue
                # Type is column index 3.
                _type = re.sub(r"<[^>]+>", "", cells[3]).strip()
                if not _type.upper().startswith(type_prefix.upper()):
                    continue
                # Document column (index 2) has the <a href>.
                _href_m = re.search(r'<a\b[^>]*href="([^"]+)"', cells[2], re.I)
                if not _href_m:
                    continue
                href = _href_m.group(1)
                # Strip XBRL inline viewer prefix.
                _ix = re.match(r"/ix\?doc=(/.+)", href)
                if _ix:
                    href = _ix.group(1)
                results.append(href)
            return results

        # Get the company filings to find the URL.
        # Domestic issuers file 10-K (annual) / 10-Q (quarterly).
        # Foreign private issuers file 40-F or 20-F (annual) and
        # 6-K (current/quarterly).  Search for all applicable forms
        # and let the most-recent-filing logic pick the right one.

        _form_types = "10-K,10-Q,40-F,20-F"

        if (
            query.symbol == "BLK" and query.calendar_year and query.calendar_year < 2025
        ) or query.symbol.isnumeric():
            filings = await SecCompanyFilingsFetcher.fetch_data(
                {
                    "cik": "0001364742" if query.symbol == "BLK" else query.symbol,
                    "form_type": _form_types,
                    "use_cache": query.use_cache,
                },
                {},
            )

        else:
            filings = await SecCompanyFilingsFetcher.fetch_data(
                {
                    "symbol": query.symbol,
                    "form_type": _form_types,
                    "use_cache": query.use_cache,
                },
                {},
            )

        if not filings:
            raise OpenBBError(
                f"Could not find any 10-K, 10-Q, 40-F, or 20-F filings for the symbol. -> {query.symbol}"
            )

        # If no calendar year or period is provided, get the most recent filing.

        target_filing: Any = None
        calendar_year: Any = None
        calendar_period: Any = None

        _is_foreign_issuer = any(
            f.report_type in ("40-F", "20-F", "40-F/A", "20-F/A")  # type: ignore
            for f in filings
        )

        if query.calendar_year is None and query.calendar_period is None:
            target_filing = (
                filings[0]  # type: ignore
                if not query.calendar_year and not query.calendar_period
                else None
            )
            # For foreign issuers the most-recent 10-K/10-Q/40-F/20-F
            # may be older than a 6-K that contains quarterly MD&A.
            # Check whether a newer 6-K with an MD&A exhibit exists.
            if target_filing and _is_foreign_issuer:
                _6k_recent = await SecCompanyFilingsFetcher.fetch_data(
                    {
                        "symbol": query.symbol if not query.symbol.isnumeric() else "",
                        "cik": query.symbol if query.symbol.isnumeric() else "",
                        "form_type": "6-K",
                        "use_cache": query.use_cache,
                    },
                    {},
                )
                if _6k_recent and _6k_recent[0].filing_date > target_filing.filing_date:  # type: ignore
                    # A more-recent 6-K exists.  Scan its index for
                    # an EX-99 exhibit with MD&A content.
                    _mda_re = re.compile(r"(?:mda|md&a|quarterly|discussion)", re.I)
                    for _6kf in _6k_recent:
                        if _6kf.filing_date <= target_filing.filing_date:  # type: ignore
                            break  # older than current pick; stop
                        _idx_url = _6kf.filing_detail_url
                        try:
                            if query.use_cache is True:
                                _cd = (
                                    f"{get_user_cache_directory()}/http/sec_financials"
                                )
                                async with CachedSession(
                                    cache=SQLiteBackend(_cd)
                                ) as _sess:
                                    try:
                                        _idx_html = await amake_request(
                                            _idx_url,  # type: ignore
                                            headers=SEC_HEADERS,
                                            response_callback=sec_callback,
                                            session=_sess,
                                        )
                                    finally:
                                        await _sess.close()
                            else:
                                _idx_html = await amake_request(
                                    _idx_url,  # type: ignore
                                    headers=SEC_HEADERS,
                                    response_callback=sec_callback,
                                )
                        except Exception:  # noqa
                            continue
                        if not isinstance(_idx_html, str):
                            continue
                        _ex99_hrefs = _extract_exhibit_links(_idx_html, "EX-99")
                        for _href in _ex99_hrefs:
                            _fname = _href.rsplit("/", 1)[-1]
                            if _mda_re.search(_fname):
                                target_filing = _6kf
                                break
                        if target_filing.report_type == "6-K":  # type: ignore
                            break

                    # Second pass: filenames didn't match.  Read the
                    # 6-K cover page for exhibit descriptions like
                    # "Q4 2025 Update", "Letter to Shareholders", etc.
                    if target_filing.report_type != "6-K":  # type: ignore
                        _cover_re = re.compile(
                            r"Q[1-4]\s+\d{4}\s+Update|"
                            r"Letter\s+to\s+Shareholders|"
                            r"Shareholder\s+Letter|"
                            r"Earnings\s+(?:Release|Update)|"
                            r"Quarterly\s+(?:Report|Update|Results)",
                            re.IGNORECASE,
                        )
                        for _6kf in _6k_recent:
                            if _6kf.filing_date <= target_filing.filing_date:  # type: ignore
                                break
                            try:
                                _cover_url = _6kf.report_url
                                if query.use_cache is True:
                                    _cd = f"{get_user_cache_directory()}/http/sec_financials"
                                    async with CachedSession(
                                        cache=SQLiteBackend(_cd)
                                    ) as _sess:
                                        try:
                                            _cover_html = await amake_request(
                                                _cover_url,
                                                headers=SEC_HEADERS,
                                                response_callback=sec_callback,
                                                session=_sess,
                                            )
                                        finally:
                                            await _sess.close()
                                else:
                                    _cover_html = await amake_request(
                                        _cover_url,
                                        headers=SEC_HEADERS,
                                        response_callback=sec_callback,
                                    )
                            except Exception:  # noqa
                                continue
                            if isinstance(_cover_html, str) and _cover_re.search(
                                _cover_html
                            ):
                                target_filing = _6kf
                                break

            # Domestic issuer: check for a more-recent 8-K that
            # contains earnings results (EX-99 exhibit) filed after
            # the latest 10-K/10-Q.  This covers the gap between
            # the earnings announcement and the formal 10-K/Q filing.
            if target_filing and not _is_foreign_issuer:
                _8k_recent = await SecCompanyFilingsFetcher.fetch_data(
                    {
                        "symbol": query.symbol if not query.symbol.isnumeric() else "",
                        "cik": query.symbol if query.symbol.isnumeric() else "",
                        "form_type": "8-K",
                        "use_cache": query.use_cache,
                    },
                    {},
                )
                if _8k_recent and _8k_recent[0].filing_date > target_filing.filing_date:  # type: ignore
                    # Item 2.02 = "Results of Operations and Financial
                    # Condition" — the standard 8-K item for earnings.
                    _8k_earnings_re = re.compile(
                        r"Item\s+2\.02|"
                        r"Results\s+of\s+Operations\s+and\s+Financial\s+Condition|"
                        r"Earnings\s+(?:Release|Press\s+Release|Update)|"
                        r"Financial\s+Results|"
                        r"Press\s+Release.*(?:Quarter|Annual|Fiscal)",
                        re.IGNORECASE,
                    )
                    for _8kf in _8k_recent:
                        if _8kf.filing_date <= target_filing.filing_date:  # type: ignore
                            break  # older than current 10-K/Q; stop
                        # Check filing index for EX-99 exhibits.
                        _idx_url = _8kf.filing_detail_url
                        try:
                            if query.use_cache is True:
                                _cd = (
                                    f"{get_user_cache_directory()}/http/sec_financials"
                                )
                                async with CachedSession(
                                    cache=SQLiteBackend(_cd)
                                ) as _sess:
                                    try:
                                        _idx_html = await amake_request(
                                            _idx_url,  # type: ignore
                                            headers=SEC_HEADERS,
                                            response_callback=sec_callback,
                                            session=_sess,
                                        )
                                    finally:
                                        await _sess.close()
                            else:
                                _idx_html = await amake_request(
                                    _idx_url,  # type: ignore
                                    headers=SEC_HEADERS,
                                    response_callback=sec_callback,
                                )
                        except Exception:  # noqa
                            continue
                        if not isinstance(_idx_html, str):
                            continue
                        _ex99_hrefs = _extract_exhibit_links(_idx_html, "EX-99")
                        if not _ex99_hrefs:
                            continue
                        # Read the 8-K filing for Item 2.02 or
                        # earnings-related language.
                        try:
                            _cover_url = _8kf.report_url
                            if query.use_cache is True:
                                _cd = (
                                    f"{get_user_cache_directory()}/http/sec_financials"
                                )
                                async with CachedSession(
                                    cache=SQLiteBackend(_cd)
                                ) as _sess:
                                    try:
                                        _cover_html = await amake_request(
                                            _cover_url,
                                            headers=SEC_HEADERS,
                                            response_callback=sec_callback,
                                            session=_sess,
                                        )
                                    finally:
                                        await _sess.close()
                            else:
                                _cover_html = await amake_request(
                                    _cover_url,
                                    headers=SEC_HEADERS,
                                    response_callback=sec_callback,
                                )
                        except Exception:  # noqa
                            continue
                        if isinstance(_cover_html, str) and _8k_earnings_re.search(
                            _cover_html
                        ):
                            target_filing = _8kf
                            break

        if not target_filing:
            if query.calendar_period and not query.calendar_year:
                calendar_year = to_datetime("today").year
                calendar_period = to_datetime("today").quarter
            elif query.calendar_year and query.calendar_period:
                calendar_year = query.calendar_year
                calendar_period = int(query.calendar_period[1])
            elif query.calendar_year:
                calendar_year = query.calendar_year
                calendar_period = 1

            if query.calendar_year and not query.calendar_period:
                target_filing = [
                    f
                    for f in filings
                    if f.report_type
                    in (  # type: ignore
                        "10-K",
                        "40-F",
                        "20-F",
                        "40-F/A",
                        "20-F/A",
                    )
                    and f.filing_date.year == query.calendar_year  # type: ignore
                ]
                if not target_filing:
                    target_filing = [
                        f
                        for f in filings
                        if f.filing_date.year == query.calendar_year  # type: ignore
                    ]
                if target_filing:
                    target_filing = target_filing[0]

            elif calendar_year and calendar_period:
                start = to_datetime(f"{calendar_year}Q{calendar_period}")
                start_date = (
                    start - offsets.QuarterBegin(1) + offsets.MonthBegin(1)
                ).date()
                end_date = (
                    start_date + offsets.QuarterEnd(0) - offsets.MonthEnd(0)
                ).date()

                for filing in filings:
                    if start_date < filing.filing_date < end_date:  # type: ignore
                        target_filing = filing
                        break

        # For foreign private issuer quarterly reports (6-K), the filing
        # list above only covers 10-K/10-Q/40-F/20-F.  When no match
        # was found for a specific quarter AND the issuer files foreign
        # forms, search 6-K filings for a quarterly report instead.
        #
        # Foreign issuers file many 6-Ks (press releases, certifications,
        # etc.).  Only a few contain quarterly results.  Strategy:
        #   1. Collect 6-Ks in the target date range.
        #   2. For each candidate, check the filing index page for an
        #      EX-99 exhibit whose filename suggests MD&A content
        #      (e.g. contains "mda", "md&a", or "quarterly").
        #   3. If none match by filename, fall back to the first 6-K
        #      whose EX-99 exhibit HTML contains "Discussion and Analysis".

        if (
            not target_filing
            and _is_foreign_issuer
            and calendar_year
            and calendar_period
        ):
            _6k_filings = await SecCompanyFilingsFetcher.fetch_data(
                {
                    "symbol": query.symbol if not query.symbol.isnumeric() else "",
                    "cik": query.symbol if query.symbol.isnumeric() else "",
                    "form_type": "6-K",
                    "use_cache": query.use_cache,
                },
                {},
            )
            if _6k_filings:
                start = to_datetime(f"{calendar_year}Q{calendar_period}")
                _6k_start_date = (
                    start - offsets.QuarterBegin(1) + offsets.MonthBegin(1)
                ).date()
                _6k_end_date = (start + offsets.QuarterEnd(0)).date()

                _candidates = [
                    f
                    for f in _6k_filings
                    if _6k_start_date <= f.filing_date <= _6k_end_date  # type: ignore
                ]

                # Try each candidate's filing index for an MD&A exhibit.
                _mda_fname_re = re.compile(
                    r"(?:mda|md&a|quarterly|discussion)", re.IGNORECASE
                )

                async def _fetch_6k(u: str) -> str | None:
                    try:
                        if query.use_cache is True:
                            _cd = f"{get_user_cache_directory()}/http/sec_financials"
                            async with CachedSession(cache=SQLiteBackend(_cd)) as _sess:
                                try:
                                    return await amake_request(  # type: ignore
                                        u,
                                        headers=SEC_HEADERS,
                                        response_callback=sec_callback,
                                        session=_sess,
                                    )
                                finally:
                                    await _sess.close()
                        return await amake_request(  # type: ignore
                            u,
                            headers=SEC_HEADERS,
                            response_callback=sec_callback,
                        )
                    except Exception:  # noqa  # pylint: disable=broad-except
                        return None

                _6k_with_ex99: list[Any] = []
                for _6kf in _candidates:
                    _idx_url = _6kf.filing_detail_url  # type: ignore
                    _idx_html = await _fetch_6k(_idx_url)  # type: ignore
                    if not isinstance(_idx_html, str):
                        continue
                    # Parse the filing index table for EX-99
                    # exhibit links (using the Type cell, not the
                    # href URL which may not contain 'ex99').
                    _ex99_hrefs = _extract_exhibit_links(_idx_html, "EX-99")
                    for _href in _ex99_hrefs:
                        _fname = _href.rsplit("/", 1)[-1]
                        if _mda_fname_re.search(_fname):
                            target_filing = _6kf
                            break
                    if target_filing:
                        break
                    if _ex99_hrefs:
                        _6k_with_ex99.append(_6kf)

                # Second pass: filename didn't match but the 6-K has
                # EX-99 exhibits.  Read the actual 6-K cover page —
                # it describes the exhibits (e.g. "Q4 2025 Update",
                # "Letter to Shareholders", "Earnings Release").
                if not target_filing and _6k_with_ex99:
                    _cover_desc_re = re.compile(
                        r"Q[1-4]\s+\d{4}\s+Update|"
                        r"Letter\s+to\s+Shareholders|"
                        r"Shareholder\s+Letter|"
                        r"Earnings\s+(?:Release|Update)|"
                        r"Quarterly\s+(?:Report|Update|Results)",
                        re.IGNORECASE,
                    )
                    for _6kf in _6k_with_ex99:
                        _cover_html = await _fetch_6k(_6kf.report_url)  # type: ignore
                        if isinstance(_cover_html, str) and _cover_desc_re.search(
                            _cover_html
                        ):
                            target_filing = _6kf
                            break

        # Domestic issuer 8-K fallback: when no 10-K/10-Q has been
        # filed yet for the requested quarter, the company may have
        # already published earnings via an 8-K press release (EX-99
        # exhibit).  Search 8-K filings in the target date range for
        # an earnings announcement.
        if (
            not target_filing
            and not _is_foreign_issuer
            and calendar_year
            and calendar_period
        ):
            _8k_filings = await SecCompanyFilingsFetcher.fetch_data(
                {
                    "symbol": query.symbol if not query.symbol.isnumeric() else "",
                    "cik": query.symbol if query.symbol.isnumeric() else "",
                    "form_type": "8-K",
                    "use_cache": query.use_cache,
                },
                {},
            )
            if _8k_filings:
                start = to_datetime(f"{calendar_year}Q{calendar_period}")
                _8k_start_date = (
                    start - offsets.QuarterBegin(1) + offsets.MonthBegin(1)
                ).date()
                _8k_end_date = (start + offsets.QuarterEnd(0)).date()

                _8k_candidates = [
                    f
                    for f in _8k_filings
                    if _8k_start_date <= f.filing_date <= _8k_end_date  # type: ignore
                ]

                async def _fetch_8k(u: str) -> str | None:
                    try:
                        if query.use_cache is True:
                            _cd = f"{get_user_cache_directory()}/http/sec_financials"
                            async with CachedSession(cache=SQLiteBackend(_cd)) as _sess:
                                try:
                                    return await amake_request(  # type: ignore
                                        u,
                                        headers=SEC_HEADERS,
                                        response_callback=sec_callback,
                                        session=_sess,
                                    )
                                finally:
                                    await _sess.close()
                        return await amake_request(  # type: ignore
                            u,
                            headers=SEC_HEADERS,
                            response_callback=sec_callback,
                        )
                    except Exception:  # noqa  # pylint: disable=broad-except
                        return None

                _earnings_desc_re = re.compile(
                    r"Q[1-4]\s+\d{4}\s+(?:Update|Results|Earnings)|"
                    r"Earnings\s+(?:Release|Press\s+Release|Update)|"
                    r"Press\s+Release|"
                    r"Quarterly\s+(?:Report|Update|Results)|"
                    r"(?:Financial|Operating)\s+Results|"
                    r"Results\s+(?:of|for)\s+Operations",
                    re.IGNORECASE,
                )

                for _8kf in _8k_candidates:
                    _idx_url = _8kf.filing_detail_url  # type: ignore
                    _idx_html = await _fetch_8k(_idx_url)  # type: ignore
                    if not isinstance(_idx_html, str):
                        continue
                    _ex99_hrefs = _extract_exhibit_links(_idx_html, "EX-99")
                    if not _ex99_hrefs:
                        continue
                    # Read the 8-K cover page for earnings description.
                    _cover_html = await _fetch_8k(_8kf.report_url)  # type: ignore
                    if isinstance(_cover_html, str) and _earnings_desc_re.search(
                        _cover_html
                    ):
                        target_filing = _8kf
                        break

        if not target_filing:
            raise OpenBBError(
                f"Could not find a filing for the symbol -> {query.symbol}"
            )

        url = target_filing.report_url
        response = ""

        if query.use_cache is True:
            cache_dir = f"{get_user_cache_directory()}/http/sec_financials"
            async with CachedSession(cache=SQLiteBackend(cache_dir)) as session:
                try:
                    await session.delete_expired_responses()
                    response = await amake_request(
                        url,
                        headers=SEC_HEADERS,
                        response_callback=sec_callback,
                        session=session,
                    )  # type: ignore
                finally:
                    await session.close()
        else:
            response = await amake_request(url, headers=SEC_HEADERS, response_callback=sec_callback)  # type: ignore

        # Some 10-K filings have a stub Item 7 that simply
        # cross-references the Annual Report to Stockholders filed as
        # Exhibit 13.  When we detect this pattern we pre-fetch the
        # exhibit so that transform_data can extract MD&A from it.
        exhibit_content: str | None = None
        exhibit_url: str | None = None
        _exhibit_is_full_document: bool = False
        _index_url: str | None = None
        _index_html: Any = None

        if isinstance(response, str) and re.search(
            r"incorporated\s+(?:herein\s+by\s+reference|by\s+reference\s+herein)",
            response,
            re.IGNORECASE,
        ):
            _base_dir = url.rsplit("/", 1)[0]

            # Strategy 1: look for an inline exhibit link in the HTML
            # (modern filings embed <a href="...">Annual Report to
            # Security Holders</a>).
            _ar_re = re.compile(
                r'<a\b[^>]*href="([^"]+)"[^>]*>[^<]*'
                r"Annual\s+Report\s+to\s+(?:Security|Stock|Share)\s*[Hh]olders"
                r"[^<]*</a>",
                re.IGNORECASE,
            )
            _m = _ar_re.search(response)

            # Strategy 2: fall back to the filing index page and look for
            # the EX-13 exhibit document (older filings).
            if not _m:
                _index_url = target_filing.filing_detail_url
                try:
                    if query.use_cache is True:
                        cache_dir = f"{get_user_cache_directory()}/http/sec_financials"
                        async with CachedSession(
                            cache=SQLiteBackend(cache_dir)
                        ) as session:
                            try:
                                _index_html = await amake_request(
                                    _index_url,
                                    headers=SEC_HEADERS,
                                    response_callback=sec_callback,
                                    session=session,
                                )
                            finally:
                                await session.close()
                    else:
                        _index_html = await amake_request(
                            _index_url,
                            headers=SEC_HEADERS,
                            response_callback=sec_callback,
                        )
                    if isinstance(_index_html, str):
                        # Parse the filing index table for EX-13 rows.
                        _ex13_hrefs = _extract_exhibit_links(_index_html, "EX-13")
                        if _ex13_hrefs:
                            _href = _ex13_hrefs[0]
                            # Index page links are usually absolute paths
                            if _href.startswith("http"):
                                _m_url = _href
                            elif _href.startswith("/"):
                                _m_url = "https://www.sec.gov" + _href
                            else:
                                _m_url = _base_dir + "/" + _href

                            # Wrap in a fake match-like object
                            class _FakeMatch:
                                def group(self, n):
                                    return _m_url if n == 1 else ""

                            _m = _FakeMatch()  # type: ignore
                except Exception:  # noqa  # pylint: disable=broad-except
                    pass  # Index page unavailable; proceed without exhibit

            if _m:
                _href = _m.group(1)
                _exhibit_url: str = (
                    _href if _href.startswith("http") else _base_dir + "/" + _href
                )
                exhibit_url = _exhibit_url
                if query.use_cache is True:
                    cache_dir = f"{get_user_cache_directory()}/http/sec_financials"
                    async with CachedSession(cache=SQLiteBackend(cache_dir)) as session:
                        try:
                            exhibit_content = await amake_request(
                                _exhibit_url,
                                headers=SEC_HEADERS,
                                response_callback=sec_callback,
                                session=session,
                            )  # type: ignore
                        finally:
                            await session.close()
                else:
                    exhibit_content = await amake_request(  # type: ignore
                        _exhibit_url,
                        headers=SEC_HEADERS,
                        response_callback=sec_callback,
                    )

        # Foreign private issuer filings (40-F / 20-F) typically do not
        # contain an inline MD&A section.  Instead, the MD&A is filed as
        # a separate exhibit (usually EX-99.2).  When we detect a foreign
        # filing, browse the filing index page for EX-99 exhibit links,
        # fetch each candidate, and use the first one that contains
        # "Discussion and Analysis" text.
        #
        # The same logic applies to domestic 8-K earnings releases:
        # the actual content lives in an EX-99 exhibit.
        _has_exhibit_content = target_filing.report_type in (
            "40-F",
            "20-F",
            "40-F/A",
            "20-F/A",
            "6-K",
            "8-K",
        )

        if isinstance(response, str) and _has_exhibit_content and not exhibit_content:
            _base_dir = url.rsplit("/", 1)[0]
            _index_url = target_filing.filing_detail_url

            async def _fetch(u: str) -> str | None:
                """Fetch a URL using cache settings."""
                try:
                    if query.use_cache is True:
                        _cd = f"{get_user_cache_directory()}/http/sec_financials"
                        async with CachedSession(cache=SQLiteBackend(_cd)) as _sess:
                            try:
                                return await amake_request(  # type: ignore
                                    u,
                                    headers=SEC_HEADERS,
                                    response_callback=sec_callback,
                                    session=_sess,
                                )
                            finally:
                                await _sess.close()
                    return await amake_request(  # type: ignore
                        u,
                        headers=SEC_HEADERS,
                        response_callback=sec_callback,
                    )
                except Exception:  # noqa  # pylint: disable=broad-except
                    return None

            _index_html = await _fetch(_index_url)  # type: ignore

            if isinstance(_index_html, str):
                # Parse the filing index table for EX-99 exhibit
                # links using the Type cell (the href URL itself
                # may not contain 'ex99' in the filename).
                _raw_hrefs = _extract_exhibit_links(_index_html, "EX-99")
                _ex99_links: list[str] = []
                for _href99 in _raw_hrefs:
                    if _href99.startswith("http"):
                        _abs99 = _href99
                    elif _href99.startswith("/"):
                        _abs99 = "https://www.sec.gov" + _href99
                    else:
                        _abs99 = _base_dir + "/" + _href99
                    if _abs99 not in _ex99_links:
                        _ex99_links.append(_abs99)

                # Fetch each exhibit and remember the HTML so we can
                # do a multi-pass match without re-downloading.
                _fetched_exhibits: list[tuple[str, str]] = []
                for _ex_url in _ex99_links:
                    _ex_html = await _fetch(_ex_url)
                    if isinstance(_ex_html, str):
                        _fetched_exhibits.append((_ex_url, _ex_html))

                # Two-pass approach: strong patterns first, weak
                # fallback second.  "MD&A" appears in many exhibits
                # (e.g. Annual Information Forms that merely mention
                # the abbreviation) so we must prefer exhibits whose
                # HTML contains the full section title.
                #
                # Pass 1 – strong: full "Management's Discussion and
                # Analysis" or "Operating and Financial Review" title.
                for _ex_url, _ex_html in _fetched_exhibits:
                    if re.search(
                        r"(?:Management|MANAGEMENT).{0,10}"
                        r"(?:Discussion|DISCUSSION)\s+and\s+"
                        r"(?:Analysis|ANALYSIS)",
                        _ex_html,
                    ) or re.search(
                        r"(?:Operating|OPERATING)\s+and\s+Financial\s+Review",
                        _ex_html,
                    ):
                        exhibit_content = _ex_html
                        exhibit_url = _ex_url
                        break

                # Pass 2 – weak fallback: "MD&A" abbreviation.
                if not exhibit_content:
                    for _ex_url, _ex_html in _fetched_exhibits:
                        if re.search(r"MD&amp;A", _ex_html):
                            exhibit_content = _ex_html
                            exhibit_url = _ex_url
                            break

                # Pass 3 – 6-K / 8-K presentation slide deck or
                # shareholder update.  When both MD&A passes fail,
                # the exhibit may be a slide deck or quarterly update
                # that does NOT contain a dedicated MD&A section.
                # Read the cover page for exhibit descriptions and
                # check the exhibit HTML for slide-deck structure.
                if (
                    not exhibit_content
                    and target_filing.report_type in ("6-K", "8-K")
                    and _fetched_exhibits
                ):
                    # (a) Slide-deck HTML fingerprint:
                    #     <div class="slide"> wrapping <img> tags.
                    for _ex_url, _ex_html in _fetched_exhibits:
                        if re.search(r'<div\b[^>]*\bclass="slide"', _ex_html, re.I):
                            exhibit_content = _ex_html
                            exhibit_url = _ex_url
                            _exhibit_is_full_document = True
                            break

                    # (b) The cover page describes the exhibit
                    #     (e.g. "Q4 2025 Update", "Letter to
                    #     Shareholders", "Earnings Release").
                    if not exhibit_content and isinstance(response, str):
                        _quarterly_desc_re = re.compile(
                            r"Q[1-4]\s+\d{4}\s+Update|"
                            r"Letter\s+to\s+Shareholders|"
                            r"Shareholder\s+Letter|"
                            r"Earnings\s+(?:Release|Update)|"
                            r"Quarterly\s+(?:Report|Update|Results)|"
                            r"Press\s+Release|"
                            r"Financial\s+Results|"
                            r"Results\s+of\s+Operations",
                            re.IGNORECASE,
                        )
                        if _quarterly_desc_re.search(response):
                            _ex_url, _ex_html = _fetched_exhibits[0]
                            exhibit_content = _ex_html
                            exhibit_url = _ex_url
                            _exhibit_is_full_document = True

                # 8-K filings often split content across multiple
                # EX-99 exhibits (e.g. EX-99.1 = press release,
                # EX-99.2 = infographics / supplemental data).
                # Combine all fetched exhibits into one HTML blob so
                # the downstream converter gets the full picture.
                if (
                    exhibit_content
                    and target_filing.report_type == "8-K"
                    and len(_fetched_exhibits) > 1
                ):
                    _extra_parts: list[str] = []
                    for _ex_url, _ex_html in _fetched_exhibits:
                        if _ex_html is not exhibit_content:
                            _extra_parts.append(_ex_html)
                    if _extra_parts:
                        # Wrap each extra exhibit so the converter
                        # treats them as separate sections.
                        for _part in _extra_parts:
                            exhibit_content += "\n<!-- additional exhibit -->\n" + _part

        if isinstance(response, str):
            result: dict[str, Any] = {
                "symbol": query.symbol,
                "calendar_year": (
                    calendar_year if calendar_year else target_filing.report_date.year
                ),
                "calendar_period": (
                    calendar_period
                    if calendar_period
                    else to_datetime(target_filing.report_date).quarter
                ),
                "period_ending": target_filing.report_date,
                "report_type": target_filing.report_type,
                "url": url,
                "content": response,
            }
            if exhibit_content and exhibit_url:
                result["exhibit_content"] = exhibit_content
                result["exhibit_url"] = exhibit_url
                if _exhibit_is_full_document:
                    result["exhibit_is_full_document"] = True
            return result

        raise OpenBBError(
            f"Unexpected response received. Expected string and got -> {response.__class__.__name__} -> {response[:100]}"
        )