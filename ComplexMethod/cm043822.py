def _row_headers(parsed_row):
            result = []
            for text, _, start in parsed_row:
                t = text.strip()
                if not t:
                    continue
                # Skip first-column labels but allow years at position 0
                if start == 0 and not is_year(t):
                    continue
                if t.startswith("(") and (
                    "million" in t.lower() or "except" in t.lower()
                ):
                    continue
                result.append((t, start))
            return result