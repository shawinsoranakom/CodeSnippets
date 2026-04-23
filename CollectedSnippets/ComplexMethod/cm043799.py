def _merge_consecutive_headers(markdown: str) -> str:
    """
    Merge consecutive headers at the same level into a single header.

    SEC filings often have titles split across multiple lines/elements:
        ### CONDENSED CONSOLIDATED STATEMENTS OF CHANGES IN
        ### STOCKHOLDERS EQUITY AND PARTNERS CAPITAL
        **(UNAUDITED)**

    This merges them into:
        ### CONDENSED CONSOLIDATED STATEMENTS OF CHANGES IN STOCKHOLDERS EQUITY AND PARTNERS CAPITAL
        **(UNAUDITED)**

    Only merges when the first header looks *incomplete* — i.e. its last
    word is a preposition, conjunction, article, or determiner.  Two
    genuinely separate headers (e.g. a section title followed by a
    subsection title) are left alone.
    """
    # Words that signal the heading phrase is incomplete.
    _CONTINUATION_ENDINGS = {
        "in",
        "of",
        "and",
        "the",
        "for",
        "to",
        "with",
        "on",
        "a",
        "an",
        "by",
        "at",
        "as",
        "or",
        "nor",
        "but",
        "from",
        "into",
        "onto",
        "upon",
        "per",
        "its",
        "their",
        "our",
        "your",
        "this",
        "that",
        "these",
        "those",
        "which",
        "who",
        "whom",
        "whose",
    }

    def _looks_incomplete(text: str) -> bool:
        """Return True if *text* appears to be an incomplete title phrase."""
        t = text.rstrip()
        if not t:
            return False
        # Ends with a continuation punctuation mark (comma, dash, colon)
        if t[-1] in (",", "\u2013", "\u2014", "-"):
            return True
        last_word = t.split()[-1].lower().rstrip(".,;:")
        return last_word in _CONTINUATION_ENDINGS

    lines = markdown.split("\n")
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Check if this is a header line
        header_match = re.match(r"^(#{1,6})\s+(.+)$", stripped)

        if header_match:
            level = header_match.group(1)  # e.g., "###"
            header_text = header_match.group(2)

            # Look ahead for consecutive headers at the same level
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()

                # Skip empty lines between consecutive headers
                if not next_line:
                    j += 1
                    continue

                # Check if next non-empty line is same-level header
                next_match = re.match(r"^(#{1,6})\s+(.+)$", next_line)
                if (
                    next_match
                    and next_match.group(1) == level
                    and _looks_incomplete(header_text)
                ):
                    # Merge this header text — first header is an
                    # incomplete phrase that continues on the next line.
                    header_text = header_text.rstrip() + " " + next_match.group(2)
                    j += 1
                elif (
                    next_match
                    and next_match.group(1) != level
                    and _looks_incomplete(header_text)
                ):
                    # Different-level header but first header is clearly
                    # incomplete — merge at the current (higher) level.
                    header_text = header_text.rstrip() + " " + next_match.group(2)
                    j += 1
                else:
                    # Not a continuation — stop merging
                    break

            # Output the merged header
            result.append(f"{level} {header_text}")
            i = j
        else:
            result.append(line)
            i += 1

    return "\n".join(result)