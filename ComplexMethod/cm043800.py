def _join_split_paragraphs(markdown: str) -> str:
    """
    Join paragraphs that were split by page breaks in SEC filings.

    Handles two patterns:
    1. Hyphenated words split across pages: "pre-" ... "tax" → "pre-tax"
    2. Sentences split at connecting words: "and" ... "acquisitions" → "and acquisitions"

    Also removes page headers that interrupt paragraphs (e.g., company name, section titles).
    """
    # First, remove common SEC filing page headers that interrupt text
    # These are bold lines that repeat throughout the document
    page_header_patterns = [
        # Company name + section continuation markers
        r"\*\*[A-Z][A-Z\s,\.&]+(?:INC\.|CORP\.|LLC|LP|L\.P\.)?\s+(?:and\s+)?(?:SUBSIDIARIES?)?\s*(?:NOTES?\s+TO\s+)?(?:CONDENSED\s+)?(?:CONSOLIDATED\s+)?(?:FINANCIAL\s+STATEMENTS?)?\s*(?:—|–|-)\s*\(Continued\)\s*(?:\(UNAUDITED\))?\*\*",
        # Just "(UNAUDITED)" on its own line
        r"^\*\*\(UNAUDITED\)\*\*$",
    ]

    for pattern in page_header_patterns:
        markdown = re.sub(pattern, "", markdown, flags=re.MULTILINE | re.IGNORECASE)

    # Clean up any resulting excessive blank lines
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)

    lines = markdown.split("\n")
    result = []
    i = 0

    # Patterns for structural lines that should never be joined
    # Note: \d{1,2}\.\s matches numbered lists (1-99) but NOT years like "2024."
    _STRUCTURAL_RE = re.compile(r"^(?:#|\||- |\* |\d{1,2}\.\s|<img|<a\s|\[)")
    # Connecting words that always indicate mid-sentence when at line end
    _CONNECTING_RE = re.compile(
        r"\b(and|or|the|a|an|of|to|in|for|with|by|from|at|on|as|that|which|but|"
        r"is|are|was|were|be|been|being|have|has|had|not|its|their|our|this|"
        r"these|those|into|upon|about|through|under|between|during|after|"
        r"before|including|such)\s*$",
        re.IGNORECASE,
    )

    def _is_joinable_line(s: str) -> bool:
        """Return True if stripped line *s* is eligible for joining."""
        return (
            bool(s)
            and not _STRUCTURAL_RE.match(s)
            and not _INLINE_HTML_RE.search(s)
            and not _PAGE_HEADER_LINK_RE.match(s)
        )

    def _next_nonblank(start: int):
        """Return (index, stripped_text) of next non-blank line, or (start, None)."""
        j = start
        while j < len(lines) and not lines[j].strip():
            j += 1
        if j < len(lines):
            return j, lines[j].strip()
        return j, None

    # Bullet prefixes that should participate in forward-joining
    _BULLET_RE = re.compile(r"^(?:- |\* |\d+\.\s)")
    # Non-bullet structural lines that should NEVER join
    _HARD_STRUCTURAL_RE = re.compile(r"^(?:#|\||\<img|\<a\s|\<div\s|\*\*Legend:\*\*)")
    # Lines containing inline HTML spans/divs are intentionally formatted;
    # they should never be joined or consumed as continuation lines.
    _INLINE_HTML_RE = re.compile(r"<(?:span|div)\s")
    # Running page headers: "Section Title [Link](#anchor)" patterns
    # that repeat on every page of the original filing.
    _PAGE_HEADER_LINK_RE = re.compile(r"^[A-Z].*\[.*\]\(#[^)]+\)\s*$")

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip blank lines and hard-structural lines (headers, tables, images)
        if (
            not stripped
            or _HARD_STRUCTURAL_RE.match(stripped)
            or _INLINE_HTML_RE.search(stripped)
            or _PAGE_HEADER_LINK_RE.match(stripped)
        ):
            result.append(line)
            i += 1
            continue

        # --- Iterative joining loop ---
        is_bullet = bool(_BULLET_RE.match(stripped))
        joined_any = True
        join_count = 0

        while joined_any:
            joined_any = False

            # 1) Hyphenated word split: "pre-" ... "tax" → "pre-tax"
            if line.rstrip().endswith("-") and not line.rstrip().endswith("--"):
                j, nxt = _next_nonblank(i + 1)

                if nxt and nxt[0].islower():
                    m = re.match(r"^(\S+)(.*)", nxt)
                    if m:
                        line = line.rstrip()[:-1] + m.group(1) + m.group(2)
                        i = j + 1
                        join_count += 1
                        joined_any = True
                        continue

            cur_stripped = line.strip()

            # 2) Line ends with a connecting word → ALWAYS continuation
            #    (regardless of next-line case)
            if _CONNECTING_RE.search(line.rstrip()):
                j, nxt = _next_nonblank(i + 1)

                if nxt and _is_joinable_line(nxt):
                    line = line.rstrip() + " " + nxt
                    i = j + 1
                    join_count += 1
                    joined_any = True
                    continue

            # 3) General mid-sentence: line does NOT end with sentence-terminal
            #    punctuation → join with next non-structural line.
            #    3a) next starts lowercase → always join
            #    3b) current line is >30 chars AND first join attempt → join
            #        (guards against runaway merging: titles/references that
            #         don't end with punctuation won't chain into the next
            #         paragraph after the first join)
            #    3c) line ends with continuation punctuation (, ; &) → join
            #        Also handles quoted forms like ,"  or ;"
            _end_stripped = cur_stripped.rstrip("\"\u201d\u2019\u2018'")
            _has_cont_punct = _end_stripped.endswith((",", ";", "&"))

            if (
                not cur_stripped.endswith((".", "!", "?", ":", '"', "\u201d"))
                or _has_cont_punct
            ):
                j, nxt = _next_nonblank(i + 1)

                if nxt and _is_joinable_line(nxt):
                    should_join = (
                        nxt[0].islower()
                        or (
                            len(cur_stripped) > 30 and join_count == 0 and not is_bullet
                        )
                        or _has_cont_punct
                    )

                    if should_join:
                        line = line.rstrip() + " " + nxt
                        i = j + 1
                        join_count += 1
                        joined_any = True
                        continue

            # 4) Abbreviation / mid-sentence period: line ends with "." but
            #    next non-blank starts lowercase → definitely a continuation
            #    (handles "U.S." / "Inc." / "No." at visual line-wrap boundary)
            if cur_stripped.endswith("."):
                j, nxt = _next_nonblank(i + 1)

                if nxt and _is_joinable_line(nxt) and nxt[0].islower():
                    line = line.rstrip() + " " + nxt
                    i = j + 1
                    join_count += 1
                    joined_any = True
                    continue

            # 5) Unclosed quote: line contains an opening " (or ")
            #    that hasn't been closed yet → we're inside a quoted
            #    reference (e.g. refer to "Part II, Item 7.)
            #    The period/punctuation is NOT sentence-terminal.
            _quote_chars = cur_stripped.count('"') + cur_stripped.count("\u201c")
            _close_chars = cur_stripped.count("\u201d")
            # For straight quotes, odd count means unclosed; for smart
            # quotes, more openers than closers means unclosed.
            _has_unclosed = (cur_stripped.count("\u201c") > _close_chars) or (
                cur_stripped.count('"') % 2 == 1
                and "\u201c" not in cur_stripped
                and "\u201d" not in cur_stripped
            )

            if _has_unclosed:
                j, nxt = _next_nonblank(i + 1)

                if nxt and _is_joinable_line(nxt):
                    line = line.rstrip() + " " + nxt
                    i = j + 1
                    join_count += 1
                    joined_any = True
                    continue

        result.append(line)
        i += 1

    return "\n".join(result)