def build_url(
        self,
        dataflow: str,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int | None = None,
        **kwargs,
    ) -> str:
        """Build the IMF SDMX REST API URL for data retrieval."""
        if dataflow not in self.metadata.dataflows:
            raise ValueError(f"Dataflow '{dataflow}' not found.")

        df = self.metadata.dataflows[dataflow]
        agency_id = df.get("agencyID")
        dsd_id = df.get("structureRef", {}).get("id")

        if not dsd_id or dsd_id not in self.metadata.datastructures:
            raise ValueError(f"Data structure not found for dataflow '{dataflow}'.")

        dsd = self.metadata.datastructures[dsd_id]
        all_dimensions = dsd.get("dimensions", [])
        dimension_ids = {d["id"] for d in all_dimensions if d.get("id")}
        # Create a map for case-insensitive matching of dimension IDs
        dimension_id_map = {d_id.lower(): d_id for d_id in dimension_ids}

        final_kwargs: dict = {}

        for key, value in kwargs.items():
            # Try to match the key (case-insensitive) to a known dimension ID
            matched_dim_id = dimension_id_map.get(key.lower())
            if matched_dim_id:
                final_kwargs[matched_dim_id] = value
            else:
                # If not a dimension, keep the original key
                final_kwargs[key] = value

        dimensions = sorted(
            [
                d
                for d in all_dimensions
                if d.get("id") is not None and d.get("position") is not None
            ],
            key=lambda x: int(x.get("position")),
        )
        key_parts: list = []
        # Use a set to keep track of dimensions that have been added to the key_parts
        # to avoid adding them again to query_params
        dimensions_in_key: set = set()

        for dim in dimensions:
            dim_id = dim.get("id")
            param_value = final_kwargs.get(dim_id)

            # Handle wildcards and empty values
            if (
                param_value is None
                or param_value in ["", "*"]
                or len(str(param_value)) > 1500
            ):
                key_parts.append("*")
            elif isinstance(param_value, list):
                key_parts.append("+".join(param_value))
            else:
                key_parts.append(str(param_value))
            dimensions_in_key.add(dim_id)

        key = ".".join(key_parts)

        if not agency_id:
            raise ValueError(f"Agency ID not found for dataflow '{dataflow}'.")

        url = (
            f"https://api.imf.org/external/sdmx/3.0/data/dataflow/"
            f"{agency_id}/{dataflow}/+/{key}"
        )
        # Only include parameters in query_params that are not dimensions
        query_params = {
            k: v for k, v in final_kwargs.items() if k not in dimensions_in_key
        }
        # Format dates for TIME_PERIOD filter
        frequency = (final_kwargs.get("FREQUENCY") or "").upper()

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

        c_params = []

        if start_date:
            formatted_start = format_date(start_date, frequency)
            c_params.append(f"ge:{formatted_start}")
        if end_date:
            formatted_end = format_date(end_date, frequency, is_end_date=True)
            c_params.append(f"le:{formatted_end}")
        if c_params:
            query_params["c[TIME_PERIOD]"] = "+".join(c_params)

        query_params = {k: v for k, v in query_params.items() if v is not None}

        if query_params:
            url += "?" + "&".join(f"{k}={v}" for k, v in query_params.items())

        url += (
            f"{'&' if '?' in url and not url.endswith('&') else '?'}"
            + "dimensionAtObservation=TIME_PERIOD&detail=full&includeHistory=false"
        )

        if limit is not None and limit > 0:
            url += f"&lastNObservations={limit}"

        return url