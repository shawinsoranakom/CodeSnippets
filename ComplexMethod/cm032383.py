def _coerce_excel_cell_type(cell: str):
            # Convert markdown cell text to native numeric types when safe,so Excel writes numeric cells instead of text.
            if not isinstance(cell, str):
                return cell

            value = cell.strip()
            if value == "":
                return ""

            # Keep values like "00123" as text to avoid losing leading zeros.
            if re.match(r"^[+-]?0\d+$", value):
                return cell

            # Support thousand separators like 1,234 or 1,234.56
            numeric_candidate = value
            if re.match(r"^[+-]?\d{1,3}(,\d{3})+(\.\d+)?$", value):
                numeric_candidate = value.replace(",", "")

            if re.match(r"^[+-]?\d+$", numeric_candidate):
                try:
                    return int(numeric_candidate)
                except ValueError:
                    return cell

            if re.match(r"^[+-]?(\d+\.\d+|\d+\.|\.\d+)([eE][+-]?\d+)?$", numeric_candidate) or re.match(r"^[+-]?\d+[eE][+-]?\d+$", numeric_candidate):
                try:
                    return float(numeric_candidate)
                except ValueError:
                    return cell

            return cell