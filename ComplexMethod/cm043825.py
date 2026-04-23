def is_data_row(row):
            col_pos = 0
            for text, cs in row:
                t = (
                    text.replace("\u200b", "")
                    .replace("\u200c", "")
                    .replace("\u200d", "")
                    .replace("\ufeff", "")
                    .strip()
                )
                if (
                    t
                    and re.match(r"^[\$]?\s*[\(\)]?\s*[\d,]+\.?\d*\s*[\)\%]?$", t)
                    and not re.match(r"^(19|20)\d{2}$", t)
                ):
                    # At position 0 (label column), a bare small number
                    # (1-3 digits with no financial formatting) may be a
                    # rendering artifact rather than a data value.
                    if col_pos == 0 and re.match(r"^\d{1,3}$", t):
                        col_pos += cs
                        continue
                    # Check if it's a year (years in header rows are ok)
                    return True
                # Also check for rating-like values (A+, A1, Prime-1, F1, Stable, etc.)
                # These are alphanumeric but short and look like data, not headers
                if t and len(t) <= 10:
                    # Short alphanumeric codes that are likely ratings/data
                    # Examples: A+, A1, Aa1, BBB+, Prime-1, F1, Stable, Positive, Negative
                    # IMPORTANT: Must end with a modifier (+/-/digit) to distinguish from words like "Tax"
                    if re.match(r"^[A-Z][a-z]{0,2}[+-][0-9]?$", t):  # A+, Aa+, Baa+
                        return True
                    if re.match(r"^[A-Z][a-z]{0,2}[0-9]$", t):  # A1, Aa1, Baa1
                        return True
                    if re.match(r"^[A-Z]{1,3}[+-]$", t):  # AA+, BBB-
                        return True
                    if re.match(r"^Prime-\d$", t):  # Prime-1
                        return True
                    if re.match(r"^[A-Z]\d$", t):  # F1
                        return True
                    # Common outlook/status values
                    if t.lower() in (
                        "stable",
                        "positive",
                        "negative",
                        "watch",
                        "developing",
                    ):
                        return True
                col_pos += cs
            return False