def is_category_text(t):
        """Check if text looks like a category header (not a year, not data)."""
        if not t or is_year(t):
            return False
        # Remove <br> tags before checking patterns (multi-line headers)
        t_clean = re.sub(r"<[Bb][Rr]\s*/?>", " ", t).strip()
        t_clean = re.sub(r"\s+", " ", t_clean)  # Collapse whitespace
        # Remove trailing footnote markers like *, **, *+, **+
        t_clean = re.sub(r"\s*[\*+]+$", "", t_clean)
        # Remove trailing superscript footnote numbers like "1,2,3" or "4"
        # These come from <sup> tags concatenated with the text
        t_clean = re.sub(r"\s+\d+(?:,\d+)*$", "", t_clean)
        # Also strip footnote digits directly attached to words (no whitespace)
        # e.g., "Net Interest2" → "Net Interest", "All Other3" → "All Other"
        t_clean = re.sub(r"(?<=[A-Za-z])\d+$", "", t_clean)
        if re.match(r"^[\$]?\s*[\(\)]?\s*[\d,]+\.?\d*\s*[\)\%]?$", t_clean):
            return False  # It's data
        # Title Case: "Equipment Operations", "Operating Income/(Loss)"
        # Strip /()\- before checking to avoid catastrophic backtracking
        t_stripped = re.sub(r"[/()\-]", " ", t_clean)
        t_stripped = re.sub(r"\s+", " ", t_stripped).strip()
        # Also prepare a variant with leading symbol prefixes removed
        # so that headers like "% Average rate" or "# of Shares" are
        # recognized after stripping the leading punctuation.
        t_no_prefix = re.sub(r"^[%#$&*~!@^]+\s*", "", t_stripped)
        if (
            re.match(r"^[A-Z][A-Za-z]*(\s+[A-Za-z&]+)*$", t_stripped)
            and len(t_clean) > 2
        ):
            return True
        if (
            t_no_prefix != t_stripped
            and re.match(r"^[A-Z][A-Za-z]*(\s+[A-Za-z&]+)*$", t_no_prefix)
            and len(t_no_prefix) > 2
        ):
            return True
        # ALL CAPS: "EQUIPMENT", "FINANCIAL SERVICES", "LONG-LIVED ASSETS"
        if re.match(r"^[A-Z]{2,}(-[A-Z]+)?(\s+[A-Z]+(-[A-Z]+)?)*$", t_clean):
            return True
        # ALL CAPS with periods/abbreviations: "WTD. AVG. EXERCISE PRICE", "NO. OF SHARES"
        # Pattern: uppercase word (optionally with period) followed by more words
        if (
            re.match(r"^[A-Z]{2,}\.?(\s+[A-Z]{2,}\.?)*(\s+[A-Z]+)*$", t_clean)
            and len(t_clean) > 3
        ):
            return True
        # Abbreviated ALL-CAPS with dots and dashes: "YR.-TO-YR."
        if re.match(r"^[A-Z]{2,}\.(-[A-Z]{2,}\.?)+$", t_clean):
            return True
        # Abbreviations like "U.S.", "NON-U.S.", "U.K." - single letters with periods
        # Pattern: optional prefix (NON-), then letter-period pairs
        if re.match(r"^([A-Z]+-)?[A-Z]\.[A-Z]\.?$", t_clean):
            return True
        # Abbreviations followed by words: "U.S. PLANS", "NON-U.S. PLANS"
        if re.match(r"^([A-Z]+-)?[A-Z]\.[A-Z]\.?(\s+[A-Z]+)+$", t_clean):
            return True
        # Hyphenated categories: "NON-GAAP", "PRE-TAX"
        if re.match(r"^[A-Z]+-[A-Z]+$", t_clean):
            return True
        # Hyphenated words followed by more words: "PPP-QUALIFIED PORTION"
        return bool(re.match(r"^[A-Z]+-[A-Z]+(\s+[A-Z]+)+$", t_clean))