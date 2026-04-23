def format_date(
            date_str: str, frequency: str, is_end_date: bool = False
        ) -> str:
            """Format date string based on frequency to match IMF TIME_PERIOD format."""
            if not date_str:
                return date_str

            # Parse the date - could be YYYY, YYYY-MM, or YYYY-MM-DD
            parts = date_str.split("-")
            year = int(parts[0])
            month = int(parts[1]) if len(parts) >= 2 else 1

            if frequency == "A" or len(parts) == 1:
                # Annual frequency or year-only input
                if is_end_date:
                    # For end date, use first day of next year
                    return f"{year + 1}-01-01"

                return f"{year}-01-01"

            if is_end_date:
                # For end date, use first day of next month
                month += 1
                if month > 12:
                    month = 1
                    year += 1

                return f"{year}-{month:02d}-01"

            return f"{year}-{month:02d}-01"