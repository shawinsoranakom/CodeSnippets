def transform_data(
        query: SecManagementDiscussionAnalysisQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> SecManagementDiscussionAnalysisData:
        """Transform the data."""
        # pylint: disable=import-outside-toplevel
        import re

        from openbb_sec.utils.html2markdown import html_to_markdown

        if query.raw_html is True:
            return SecManagementDiscussionAnalysisData(**data)

        filing_html = data.get("content", "")
        base_url = data.get("url", "")
        report_type = data.get("report_type", "")
        is_quarterly = report_type.endswith("Q")
        is_20f = report_type in ("20-F", "20-F/A")

        # Convert the full HTML filing to markdown.
        markdown = html_to_markdown(
            filing_html,
            base_url=base_url,
            keep_tables=query.include_tables,
        )

        if not markdown:
            raise EmptyDataError(
                "No content was found in the filing after HTML-to-Markdown conversion."
                f" -> {data.get('url', '')}"
                " -> The content can be analyzed by setting"
                " `raw_html=True` in the query."
            )

        # Strip leftover HTML anchor tags that the converter may leave
        # (e.g. <a id="item_2_management"></a>).  These interfere with
        # line-start-anchored regex matching.
        markdown = re.sub(r"<a\s[^>]*>\s*</a>", "", markdown)
        # Strip leading "Table of Contents" breadcrumb links that XBRL
        # authoring tools (e.g. Workiva) insert at the start of every
        # section.  These are internal markdown links like
        #   [Table of Contents](#hash)
        # or split variants like [Tab](#hash)[le of Contents](#hash).
        # They prevent ^-anchored regex patterns from matching Item
        # headers reliably.
        markdown = re.sub(
            r"^(?:\[[^\]]*\]\(#[^)]*\)\s*)+", "", markdown, flags=re.MULTILINE
        )

        def _normalize_toc_table(md: str) -> str:
            """Normalize a mangled Table of Contents markdown table.

            Foreign-filer exhibits (and some domestic filings) include a
            TOC rendered as an HTML table with colspan-driven multi-
            column layouts.  The converter produces markdown rows with
            varying column counts (4–7 cells per row).  This helper
            detects the TOC table and re-builds it as a clean 4-column
            table:  Page | Section | Page | Section.
            """
            _toc_hdr = re.compile(
                r"^\|[^\n]*Table\s+of\s+Contents[^\n]*\|",
                re.MULTILINE,
            )
            m = _toc_hdr.search(md)
            if not m:
                return md

            # Locate the full table block.
            toc_start = md.rfind("\n", 0, m.start())
            toc_start = toc_start + 1 if toc_start >= 0 else m.start()
            # Advance past the header line's trailing newline.
            toc_end = m.end()
            first_nl = md.find("\n", toc_end)
            if first_nl >= 0:
                toc_end = first_nl + 1
            while toc_end < len(md):
                nl = md.find("\n", toc_end)
                if nl < 0:
                    toc_end = len(md)
                    break
                next_line = md[toc_end:nl].strip()
                if next_line.startswith("|"):
                    toc_end = nl + 1
                else:
                    toc_end = nl
                    break

            toc_block = md[toc_start:toc_end]
            _link_re = re.compile(r"\[([^\]]*)\]\((#[^)]*)\)")

            new_rows: list[tuple[str, str, str, str]] = []
            for _toc_row in toc_block.splitlines():
                _toc_row = _toc_row.strip()
                if not _toc_row.startswith("|") or _toc_row.startswith("|---"):
                    continue
                cells = [c.strip() for c in _toc_row.strip("|").split("|")]
                if any("Table of Contents" in c for c in cells):
                    continue

                # Pair up (page_link, section_name) from non-empty cells.
                non_empty = [(i, c) for i, c in enumerate(cells) if c]
                pairs: list[tuple[str, str]] = []
                j = 0
                while j < len(non_empty):
                    _, val = non_empty[j]
                    if _link_re.match(val) or val.isdigit():
                        sect = non_empty[j + 1][1] if j + 1 < len(non_empty) else ""
                        pairs.append((val, sect))
                        j += 2
                    else:
                        pairs.append(("", val))
                        j += 1

                if len(pairs) == 1:
                    new_rows.append((pairs[0][0], pairs[0][1], "", ""))
                elif len(pairs) >= 2:
                    new_rows.append(
                        (pairs[0][0], pairs[0][1], pairs[1][0], pairs[1][1])
                    )

            if not new_rows:
                return md

            toc_lines = ["| Table of Contents | | | |", "|---|---|---|---|"]
            for p1, s1, p2, s2 in new_rows:
                toc_lines.append(f"| {p1} | {s1} | {p2} | {s2} |")
            toc_lines.append("")
            return md[:toc_start] + "\n".join(toc_lines) + md[toc_end:]

        markdown = _normalize_toc_table(markdown)

        lines = markdown.splitlines()
        # Matches an Item 7 / Item 2 header for MD&A (the formal SEC item).
        item_header_re = re.compile(
            r"^(?:#{1,4}\s*)?(?:\*{1,2})?\s*"
            r"(?:Part\s+(?:I{1,2}|1|2)[\.\s,\-\u2013\u2014]*\s*)?"
            r"(?:ITEM|Item)\s*(?:7|2)"
            r"[\.\s\-\u2013\u2014:]*"
            r"(?:Management.s|MANAGEMENT.S)\s+Discussion",
            re.IGNORECASE,
        )
        # When we see a bare Item header we check the next non-blank line for the
        # MD&A title.
        bare_item_re = re.compile(
            r"^(?:#{1,4}\s*)?(?:\*{1,2})?\s*"
            r"(?:Part\s+(?:I{1,2}|1|2)[\.\s,\-\u2013\u2014]*\s*)?"
            r"(?:ITEM|Item)\s*(?:7|2)"
            r"\s*[\.\-\u2013\u2014:]*\s*$",
            re.IGNORECASE,
        )
        mda_title_re = re.compile(
            r"^(?:#{1,4}\s*)?(?:\*{1,2})?\s*"
            r"(?:Management.s|MANAGEMENT.S)\s+Discussion",
            re.IGNORECASE,
        )

        standalone_mda_re = re.compile(
            r"^(?:#{1,4}\s*)?\*{0,2}\s*"
            r"(?:Management.s|MANAGEMENT.S)\s+Discussion\s+and\s+Analysis",
            re.IGNORECASE,
        )

        # -- 20-F: Item 5 "Operating and Financial Review and Prospects" --
        # Foreign private issuers filing on Form 20-F use Item 5 instead
        # of Item 7 for the MD&A-equivalent section.
        item5_header_re = re.compile(
            r"^(?:#{1,4}\s*)?(?:\*{1,2})?\s*"
            r"(?:Part\s+(?:I{1,2}|1|2)[\.\s,\-\u2013\u2014]*\s*)?"
            r"(?:ITEM|Item)\s*5"
            r"[\.\s\-\u2013\u2014:]*"
            r"(?:Operating|OPERATING)\s+and\s+Financial\s+Review",
            re.IGNORECASE,
        )
        bare_item5_re = re.compile(
            r"^(?:#{1,4}\s*)?(?:\*{1,2})?\s*"
            r"(?:Part\s+(?:I{1,2}|1|2)[\.\s,\-\u2013\u2014]*\s*)?"
            r"(?:ITEM|Item)\s*5"
            r"\s*[\.\-\u2013\u2014:]*\s*$",
            re.IGNORECASE,
        )
        item5_title_re = re.compile(
            r"^(?:#{1,4}\s*)?(?:\*{1,2})?\s*"
            r"(?:Operating|OPERATING)\s+and\s+Financial\s+Review",
            re.IGNORECASE,
        )
        standalone_item5_re = re.compile(
            r"^(?:#{1,4}\s*)?\*{0,2}\s*"
            r"(?:Operating|OPERATING)\s+and\s+Financial\s+Review"
            r"\s+and\s+Prospects",
            re.IGNORECASE,
        )

        # Any Item header (to detect section boundaries).
        any_item_re = re.compile(
            r"^(?:#{1,4}\s*)?\*{0,2}\s*" + r"(?:ITEM|Item)\s*\d",
            re.IGNORECASE,
        )

        # End-of-section patterns.
        end_patterns_quarterly = [
            re.compile(
                r"^(?:#{1,4}\s*)?\*{0,2}\s*"
                r"(?:ITEM|Item)\s*(?:3|4)"
                r"[.\s\-\u2013\u2014:]",
                re.IGNORECASE,
            ),
            re.compile(
                r"^(?:#{1,4}\s*)?\*{0,2}\s*SIGNATURES",
                re.IGNORECASE,
            ),
        ]

        end_patterns_annual = [
            re.compile(
                r"^(?:#{1,4}\s*)?\*{0,2}\s*"
                r"(?:ITEM|Item)\s*(?:7A|8)"
                r"[.\s\-\u2013\u2014:]",
                re.IGNORECASE,
            ),
            re.compile(
                r"^(?:#{1,4}\s*)?\*{0,2}\s*"
                r"(?:Financial\s+Statements\s+and\s+Supplementary\s+Data"
                r"|FINANCIAL\s+STATEMENTS)",
                re.IGNORECASE,
            ),
            re.compile(
                r"^(?:#{1,4}\s*)?\*{0,2}\s*SIGNATURES",
                re.IGNORECASE,
            ),
            re.compile(
                r"^(?:#{1,4}\s*)?\*{0,2}\s*PART\s+IV",
                re.IGNORECASE,
            ),
        ]

        # 20-F end patterns: Item 6 ("Directors, Senior Management …"),
        # SIGNATURES, or PART III/IV mark the end of Item 5.
        end_patterns_20f = [
            re.compile(
                r"^(?:#{1,4}\s*)?\*{0,2}\s*"
                r"(?:ITEM|Item)\s*(?:6)"
                r"[.\s\-\u2013\u2014:]",
                re.IGNORECASE,
            ),
            re.compile(
                r"^(?:#{1,4}\s*)?\*{0,2}\s*SIGNATURES",
                re.IGNORECASE,
            ),
            re.compile(
                r"^(?:#{1,4}\s*)?\*{0,2}\s*PART\s+(?:III|IV)",
                re.IGNORECASE,
            ),
        ]

        if is_20f:
            end_patterns = end_patterns_20f
        elif is_quarterly:
            end_patterns = end_patterns_quarterly
        else:
            end_patterns = end_patterns_annual

        # Select active header patterns based on filing type.
        # 20-F uses Item 5 / "Operating and Financial Review";
        # 10-K / 10-Q use Item 7/2 / "Management's Discussion".
        if is_20f:
            _active_header_re = item5_header_re
            _active_bare_re = bare_item5_re
            _active_title_re = item5_title_re
            _active_standalone_re = standalone_item5_re
        else:
            _active_header_re = item_header_re
            _active_bare_re = bare_item_re
            _active_title_re = mda_title_re
            _active_standalone_re = standalone_mda_re

        def _find_end(start: int) -> int:
            """Find the end line index for a section starting at *start*."""
            body_lines = 0
            for j in range(start + 1, len(lines)):
                stripped = lines[j].strip()
                if not stripped:
                    continue
                body_lines += 1
                if body_lines > 15:
                    for pat in end_patterns:
                        if pat.search(stripped):
                            return j
            return len(lines)

        def _is_stub(start: int) -> bool:
            """Return True if the section at *start* is a stub / cross-ref.

            A stub is a very short section (< 500 chars of body text) that
            either contains a cross-reference phrase or is immediately
            followed by another Item header with no real body content.
            """
            # Gather text until the next Item header or end of document.
            body_chars: list[str] = []
            for j in range(start + 1, min(start + 30, len(lines))):
                stripped = lines[j].strip()

                if not stripped:
                    continue
                # Hit another Item header → the section between is the body.

                if any_item_re.match(stripped):
                    break

                body_chars.append(stripped)

            body_text = " ".join(body_chars)
            # If the body is substantial, it's not a stub.
            if len(body_text) > 500:
                return False
            # Short body — check for cross-reference language.
            crossref_re = re.compile(
                r"see\s+(?:the\s+)?(?:information|discussion)|"
                r"(?:is|are)\s+(?:presented|included|incorporated)\s+(?:in|by)|"
                r"incorporated\s+herein\s+by\s+reference|"
                r"(?:refer|refers)\s+to\s+(?:Item|Part|the\s+section|pages?\s+\d)|"
                r"included\s+(?:elsewhere|herein|in\s+(?:Part|Item))|"
                r"set\s+forth\s+(?:in|under|below)|"
                r"appears?\s+on\s+page|"
                r"begins?\s+on\s+page|"
                r"found\s+(?:on|in)\s+(?:page|section)|"
                r"(?:should|must)\s+be\s+read\s+in\s+conjunction|"
                r"contained\s+(?:in|on)\s+page|"
                r"(?:is|are)\s+(?:set\s+forth|described|discussed)\s+(?:in|on|under)",
                re.IGNORECASE,
            )
            if crossref_re.search(body_text):
                return True
            # Very short body with no cross-ref — still a stub if nearly empty.
            return len(body_text) < 100

        # -- main extraction --------------------------------------------------

        # Strategy:
        #  1. Find all Item header matches (Item 7/2 for 10-K/Q,
        #     Item 5 for 20-F).
        #  2. For each, check body length to determine stub vs real.
        #  3. If all are stubs, fall back to standalone heading.

        best_start: int | None = None
        best_end: int | None = None
        _stub_anchor_id: str | None = None

        for i, line in enumerate(lines):
            stripped = line.strip()

            if not stripped:
                continue

            if _active_header_re.search(stripped):
                if _is_stub(i):
                    # Check for an internal anchor link pointing to
                    # the actual MD&A content elsewhere in the same
                    # filing (e.g., in a "Financial Section").
                    if not _stub_anchor_id:
                        _am = re.search(r"\[[^\]]*\]\(#([^)]+)\)", stripped)
                        if not _am:
                            for k in range(i + 1, min(i + 5, len(lines))):
                                ks = lines[k].strip()
                                if ks:
                                    _am = re.search(
                                        r"\[[^\]]*\]\(#([^)]+)\)",
                                        ks,
                                    )
                                    break
                        if _am:
                            _stub_anchor_id = _am.group(1)
                    continue
                best_start = i
                best_end = _find_end(i)
                break
            # Handle split headers: "Item 2." on one line, MD&A title on next.
            if _active_bare_re.search(stripped):
                # Look at the next non-blank line for the section title.
                for k in range(i + 1, min(i + 4, len(lines))):
                    next_stripped = lines[k].strip()

                    if not next_stripped:
                        continue

                    if _active_title_re.search(next_stripped) and not _is_stub(i):
                        best_start = i
                        best_end = _find_end(i)
                    break  # Only check up to the first non-blank line

                if best_start is not None:
                    break

        # Fallback: standalone section heading without Item number.
        if best_start is None:
            for i, line in enumerate(lines):
                stripped = line.strip()

                if not stripped:
                    continue

                if _active_standalone_re.search(stripped) and not _is_stub(i):
                    candidate_end = _find_end(i)
                    body = "\n".join(lines[i:candidate_end]).strip()

                    if len(body) > 200:
                        best_start = i
                        best_end = candidate_end
                        break

        # -- Internal cross-reference extraction --
        # Some filings (e.g., Chevron, ExxonMobil 10-K) place the full
        # MD&A in a "Financial Section" appended to the same document.
        # The formal Item 7 is a one-line stub such as:
        #   "Reference is made to [MD&A title](#anchor) in the
        #    Financial Section of this report."
        # Follow the embedded anchor link directly to the referenced
        # section in the raw HTML, extract it, and convert it.
        #
        # When a stub anchor is available the anchor-based extraction
        # always takes priority.  The main markdown-level extraction
        # may also find a ``best_start`` inside the Financial Section,
        # but ``_find_end()`` cannot reliably determine the section
        # boundary because the Financial Section uses its own heading
        # structure (no Item 7A / Item 8 headers).  The anchor-based
        # path reads the Table of Contents that precedes the Financial
        # Section and uses its anchor IDs to cut precisely.

        if _stub_anchor_id:
            _anchor_tag = f'id="{_stub_anchor_id}"'
            _anchor_pos = filing_html.find(_anchor_tag)
            if _anchor_pos >= 0:
                # Skip past the closing '>' of the anchor element.
                _gt = filing_html.find(">", _anchor_pos)
                _start = _gt + 1 if _gt >= 0 else _anchor_pos
                _remainder = filing_html[_start:]

                # ── Locate the end of the MD&A section ──────────────
                # The remainder begins with a Financial Table of
                # Contents whose <a href="#anchor"> links enumerate
                # every section.  Parse those links and find the first
                # anchor whose title indicates a post-MD&A section
                # (financial statements, auditor reports, etc.).
                # Cutting at the target anchor's ``id="…"`` attribute
                # is far more reliable than regex-matching section
                # titles in raw HTML (which may appear inside TOC
                # links, cross-references, etc.).

                _href_re = re.compile(
                    r'href="#([^"]+)"[^>]*>(.*?)</a>',
                    re.DOTALL | re.IGNORECASE,
                )
                _post_mda_pats = [
                    re.compile(
                        r"Consolidated\s+Financial\s+Statements",
                        re.IGNORECASE,
                    ),
                    re.compile(r"Reports?\s+of\s+Management", re.IGNORECASE),
                    re.compile(
                        r"Report\s+of\s+Independent\s+Registered",
                        re.IGNORECASE,
                    ),
                    re.compile(
                        r"To\s+the\s+(?:Stockholders|Shareholders" + r"|Board)",
                        re.IGNORECASE,
                    ),
                    re.compile(
                        r"Financial\s+Statements\s+and\s+" + r"Supplementary",
                        re.IGNORECASE,
                    ),
                    re.compile(
                        r"Changes\s+in\s+and\s+Disagreements",
                        re.IGNORECASE,
                    ),
                ]

                # Scan the TOC area (first ~80 KB should be enough).
                _toc_chunk = _remainder[:80_000]
                _end_anchor_id: str | None = None
                _start_anchor_id: str | None = None
                _seen_toc: set[str] = set()

                # Pattern to detect the MD&A section header in the TOC
                # so we can skip the TOC itself and start at the real
                # content.
                _mda_title_pat = re.compile(
                    r"Management.s\s+Discussion\s+and\s+Analysis",
                    re.IGNORECASE,
                )

                for _hm in _href_re.finditer(_toc_chunk):
                    _aid = _hm.group(1)
                    _raw = re.sub(r"<[^>]+>", " ", _hm.group(2))
                    _raw = re.sub(r"\s+", " ", _raw).strip()
                    for _ent, _ch in (
                        ("&#8217;", "\u2019"),
                        ("&#x2019;", "\u2019"),
                        ("&rsquo;", "\u2019"),
                        ("&#160;", " "),
                        ("&amp;", "&"),
                        ("&#8212;", "\u2014"),
                    ):
                        _raw = _raw.replace(_ent, _ch)
                    if len(_raw) < 4 or _aid in _seen_toc:
                        continue
                    _seen_toc.add(_aid)

                    # Track the first MD&A header anchor (to skip TOC).
                    if not _start_anchor_id and _mda_title_pat.search(_raw):
                        _start_anchor_id = _aid

                    for _pp in _post_mda_pats:
                        if _pp.search(_raw):
                            _end_anchor_id = _aid
                            break
                    if _end_anchor_id:
                        break

                # Determine HTML slice boundaries.
                # Back up to the opening '<' of the element that carries
                # the id attribute so we don't splice mid-tag and leak
                # raw attribute text into the markdown output.
                _html_start = 0
                if _start_anchor_id:
                    _start_tag = f'id="{_start_anchor_id}"'
                    _sp = _remainder.find(_start_tag)
                    if _sp > 0:
                        _lt = _remainder.rfind("<", 0, _sp)
                        _html_start = _lt if _lt >= 0 else _sp

                _cut = len(_remainder)
                if _end_anchor_id:
                    _end_tag = f'id="{_end_anchor_id}"'
                    _end_pos = _remainder.find(_end_tag)
                    if _end_pos > _html_start:
                        _cut = _end_pos

                _section_md = html_to_markdown(
                    f"<html><body>{_remainder[_html_start:_cut]}</body></html>",
                    base_url=base_url,
                    keep_tables=query.include_tables,
                )
                if _section_md and len(_section_md.strip()) > 500:
                    # Strip repeated running page headers that appear
                    # at the top of every page in the original filing
                    # (e.g., CVX 10-K: "Management's Discussion …
                    # [Financial Table of Contents](#anchor)").
                    _section_md = re.sub(
                        r"^Management.s\s+Discussion\s+and\s+Analysis"
                        r"\s+of\s+Financial\s+Condition\s+and\s+Results"
                        r"\s+of\s+Operations[^\n]*$\n?",
                        "",
                        _section_md,
                        flags=re.MULTILINE | re.IGNORECASE,
                    )
                    # Strip standalone "[Financial Table of Contents](#…)"
                    # or "[Table of Contents](#…)" breadcrumb lines.
                    _section_md = re.sub(
                        r"^\[(?:Financial\s+)?Table\s+of\s+Contents\]"
                        r"\(#[^)]+\)[^\n]*$\n?",
                        "",
                        _section_md,
                        flags=re.MULTILINE | re.IGNORECASE,
                    )
                    data["content"] = _section_md.strip()
                    return SecManagementDiscussionAnalysisData(**data)

        # -- Exhibit fallback: Annual Report / Foreign Filing Exhibits ---
        # When the main document only has a stub Item 7 (10-K) or is a
        # foreign private issuer filing (40-F / 20-F) whose MD&A lives
        # in a separately filed exhibit (EX-13 or EX-99.x),
        # aextract_data pre-fetched the exhibit HTML.

        if best_start is None and data.get("exhibit_content"):
            exhibit_base_url = data.get("exhibit_url", "")
            exhibit_md = html_to_markdown(
                data["exhibit_content"],
                base_url=exhibit_base_url,
                keep_tables=query.include_tables,
            )
            exhibit_md = re.sub(r"<a\s[^>]*>\s*</a>", "", exhibit_md)
            exhibit_md = re.sub(
                r"^(?:\[[^\]]*\]\(#[^)]*\)\s*)+",
                "",
                exhibit_md,
                flags=re.MULTILINE,
            )
            exhibit_md = _normalize_toc_table(exhibit_md)
            exhibit_lines = exhibit_md.splitlines()
            _exhibit_start_re = re.compile(
                r"^(?:#{1,4}\s*)?\*{0,2}\s*"
                r"(?:"
                r"(?:Management|MANAGEMENT).{0,3}s?\s+"
                r"(?:Discussion|DISCUSSION)"
                r"|(?:Operating|OPERATING)\s+and\s+Financial\s+Review"
                r")",
                re.IGNORECASE,
            )
            _exhibit_end_re = re.compile(
                r"^(?:#{1,4}\s*)?\*{0,2}\s*(?:"
                r"Management\s+Responsibility\s+for\s+Financial|"
                r"Management.s\s+Report\s+on\s+Internal\s+Control|"
                r"Report\s+of\s+(?:Management|Independent)|"
                r"Consolidated\s+(?:Balance\s+Sheet|Statement|Financial)|"
                r"Notes?\s+to\s+(?:Consolidated\s+)?Financial"
                r")",
                re.IGNORECASE,
            )

            for i, eline in enumerate(exhibit_lines):
                estripped = eline.strip()
                if not estripped or estripped.startswith("|"):
                    continue
                if _exhibit_start_re.search(estripped):
                    end = len(exhibit_lines)
                    body_count = 0
                    for j in range(i + 1, len(exhibit_lines)):
                        sj = exhibit_lines[j].strip()
                        if not sj:
                            continue
                        body_count += 1
                        if body_count > 15 and _exhibit_end_re.search(sj):
                            end = j
                            break
                    _content = "\n".join(exhibit_lines[i:end]).strip()
                    if len(_content) > 200:
                        data["content"] = _content
                        data["url"] = exhibit_base_url
                        return SecManagementDiscussionAnalysisData(**data)

            # Full-document fallback: 6-K presentation slide decks
            # and shareholder updates / earnings releases lack a
            # dedicated MD&A section.  Return the entire converted
            # exhibit content (with embedded markdown images).
            if (
                data.get("exhibit_is_full_document")
                and exhibit_md
                and len(exhibit_md.strip()) > 100
            ):
                data["content"] = exhibit_md.strip()
                data["url"] = exhibit_base_url
                return SecManagementDiscussionAnalysisData(**data)

        if best_start is None:
            raise EmptyDataError(
                "Could not locate the MD&A section in the filing."
                f" -> {data.get('url', '')}"
                " -> The content can be analyzed by setting"
                " `raw_html=True` in the query."
            )

        if best_end is None:
            best_end = len(lines)

        mda_content = "\n".join(lines[best_start:best_end]).strip()

        # Strip repeated running page headers (see stub-path comment).
        mda_content = re.sub(
            r"^Management.s\s+Discussion\s+and\s+Analysis"
            r"\s+of\s+Financial\s+Condition\s+and\s+Results"
            r"\s+of\s+Operations[^\n]*$\n?",
            "",
            mda_content,
            flags=re.MULTILINE | re.IGNORECASE,
        )
        # Strip standalone "[Financial Table of Contents](#…)" breadcrumb lines.
        mda_content = re.sub(
            r"^\[(?:Financial\s+)?Table\s+of\s+Contents\]" + r"\(#[^)]+\)[^\n]*$\n?",
            "",
            mda_content,
            flags=re.MULTILINE | re.IGNORECASE,
        )

        if not mda_content:
            raise EmptyDataError(
                "The MD&A section appears to be empty after extraction."
                f" -> {data.get('url', '')}"
                " -> The content can be analyzed by setting"
                " `raw_html=True` in the query."
            )

        # Ensure the section header has a markdown heading prefix and is
        # separated from any inline body text.  Many filings emit the
        # Item header as plain text (no <h1>/<h2> tag), so the converter
        # never inserts a '#' prefix.
        #
        # Detection strategy: ALL-CAPS words at the start of the content
        # form the section title (e.g. "ITEM 2. MANAGEMENT'S DISCUSSION
        # AND ANALYSIS …").  The title may span multiple lines; it ends
        # at the first word containing a lowercase letter.  For mixed-case
        # filings that use "Item N." we simply prepend '#'.
        mda_lines = mda_content.splitlines()
        if mda_lines:
            first = mda_lines[0].strip()
            if not first.startswith("#"):
                # Collect words from the opening lines, noting where the
                # first lowercase word appears (= end of ALL-CAPS title).
                all_words: list[str] = []
                lines_consumed = 0
                split_idx: int | None = None  # index of first lowercase word

                for i in range(min(len(mda_lines), 6)):
                    line = mda_lines[i].strip()
                    if not line:
                        lines_consumed = i + 1
                        break
                    for w in line.split():
                        if re.search(r"[a-z]", w) and split_idx is None:
                            split_idx = len(all_words)
                        all_words.append(w)
                    lines_consumed = i + 1
                    if split_idx is not None:
                        break

                if split_idx is not None:
                    title_text = " ".join(all_words[:split_idx])
                    body_text = " ".join(all_words[split_idx:])
                else:
                    title_text = " ".join(all_words)
                    body_text = ""

                is_caps_title = (
                    bool(title_text) and re.match(r"ITEM\s+\d", title_text) is not None
                )

                if is_caps_title:
                    new_lines = ["## " + title_text, ""]
                    if body_text:
                        new_lines.append(body_text)
                    mda_lines = new_lines + mda_lines[lines_consumed:]
                elif re.match(r"Item\s+\d", first, re.IGNORECASE):
                    # Mixed-case "Item N." header — just add '#' prefix.
                    mda_lines[0] = "## " + first

                mda_content = "\n".join(mda_lines)

        data["content"] = mda_content

        return SecManagementDiscussionAnalysisData(**data)