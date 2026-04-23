def is_header_text(t):
            if not t:
                return False
            # Remove zero-width chars
            t = (
                t.replace("\u200b", "")
                .replace("\u200c", "")
                .replace("\u200d", "")
                .replace("\ufeff", "")
                .strip()
            )
            if not t:
                return False
            # Years are headers
            if re.match(r"^(19|20)\d{2}$", t):
                return True
            # Year-range labels like "2009 -", "2011 –", "2013-" are headers
            # (the trailing dash signals the start of a date range spanning the
            # child row, e.g. "2009 - 2010").
            if re.match(r"^(19|20)\d{2}\s*[\-\u2013\u2014]", t):
                return True
            # Data patterns - not headers
            if re.match(r"^[\$]?\s*[\(\)]?\s*[\d,]+\.?\d*\s*[\)\%]?$", t):
                return False
            # Single punctuation - not a header
            if len(t) <= 1:
                return False
            # Numeric range labels like "0 - 6", "6 - 12", "1 - 5" are maturity
            # bucket column headers — they contain no letters but are clearly headers.
            if re.match(r"^\d+\s*[-\u2013\u2014]\s*\d+$", t):
                return True
            # Text with letters is likely a header
            return bool(re.search(r"[A-Za-z]", t))