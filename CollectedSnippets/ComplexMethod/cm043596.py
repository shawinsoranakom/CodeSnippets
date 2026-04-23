def transform_data(
        query: FederalReserveSvenssonQueryParams,
        data: str,
        **kwargs: Any,
    ) -> list[FederalReserveSvenssonData]:
        """Transform the CSV data into a list of FederalReserveSvenssonData objects."""
        # pylint: disable=import-outside-toplevel
        import csv
        from datetime import datetime
        from io import StringIO

        csv_to_field = {
            v: k for k, v in FederalReserveSvenssonData.__alias_dict__.items()
        }
        allowed_fields: set[str] | None = None

        # Parse comma-separated series_type into a list
        series_types = [s.strip().lower() for s in query.series_type.split(",")]

        if "all" not in series_types:
            allowed_fields = {"date"}

            for series_type in series_types:
                if series_type == "zero_coupon":
                    allowed_fields.update(f"sveny{i:02d}" for i in range(1, 31))
                elif series_type == "par_yield":
                    allowed_fields.update(f"svenpy{i:02d}" for i in range(1, 31))
                elif series_type == "forward_instantaneous":
                    allowed_fields.update(f"svenf{i:02d}" for i in range(1, 31))
                elif series_type == "forward_1y":
                    allowed_fields.update({"sven1f01", "sven1f04", "sven1f09"})
                elif series_type == "parameters":
                    allowed_fields.update(
                        {"beta0", "beta1", "beta2", "beta3", "tau1", "tau2"}
                    )
                else:
                    # Individual column selection
                    allowed_fields.add(series_type)

        # Find the line starting with "Date," which is the real column header.
        lines = data.split("\n")
        header_index = next(
            (i for i, line in enumerate(lines) if line.startswith("Date,")),
            None,
        )

        if header_index is None:
            raise OpenBBError("Could not find the header row in the CSV data.")

        csv_content = "\n".join(lines[header_index:])
        reader = csv.DictReader(StringIO(csv_content))
        results: list[FederalReserveSvenssonData] = []

        for row in reader:
            date_str = row.get("Date", "")
            if not date_str:
                continue

            try:
                row_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                continue

            if query.start_date and row_date < query.start_date:
                continue

            if query.end_date and row_date > query.end_date:
                continue

            filtered_row: dict[str, Any] = {}
            for csv_col, value in row.items():
                field_name = csv_to_field.get(csv_col)

                if field_name is None:
                    continue

                if allowed_fields is not None and field_name not in allowed_fields:
                    continue

                filtered_row[field_name] = value

            if filtered_row:
                results.append(FederalReserveSvenssonData(**filtered_row))

        if not results:
            raise OpenBBError(
                "The query filters resulted in no data. Try again with different parameters."
            )

        return results