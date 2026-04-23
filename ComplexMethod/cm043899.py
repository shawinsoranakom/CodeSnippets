def parse_and_validate_symbols(self):
        """Parse symbols and validate table/indicator constraints."""
        # pylint: disable=import-outside-toplevel
        from openbb_imf.utils.metadata import ImfMetadata

        if not self.symbol:
            raise ValueError("symbol is required.")

        country_dimensions = {"COUNTRY", "REF_AREA", "JURISDICTION", "AREA"}
        frequency_dimensions = {"FREQUENCY", "FREQ"}
        transform_dimensions = {
            "UNIT_MEASURE",
            "UNIT",
            "TRANSFORMATION",
            "TYPE_OF_TRANSFORMATION",
        }

        remaining_dimension_values: list[str] = []

        if self.dimension_values:
            for dv in self.dimension_values:
                if ":" not in dv:
                    remaining_dimension_values.append(dv)
                    continue
                dim_id, dim_value = dv.split(":", 1)
                dim_id_upper = dim_id.strip().upper()
                dim_value = dim_value.strip()

                # dimension_values OVERRIDES the country parameter
                if dim_id_upper in country_dimensions:
                    object.__setattr__(self, "country", dim_value)
                # dimension_values OVERRIDES the frequency parameter
                elif dim_id_upper in frequency_dimensions:
                    object.__setattr__(self, "frequency", dim_value)
                # dimension_values OVERRIDES the transform parameter
                elif dim_id_upper in transform_dimensions:
                    object.__setattr__(self, "transform", dim_value)
                # Keep dimension_values that are not consumed by country/frequency/transform
                else:
                    remaining_dimension_values.append(dv)

            # Update dimension_values to only contain non-consumed dimensions
            object.__setattr__(
                self,
                "dimension_values",
                remaining_dimension_values if remaining_dimension_values else None,
            )

        # Validate country requirement - must have country by now
        if not self.country:
            raise ValueError(
                "Country is required. Provide via 'country' parameter or include a country "
                "dimension (COUNTRY, REF_AREA, JURISDICTION, AREA) in 'dimension_values'."
            )

        symbols = [
            s.strip()
            for s in self.symbol.split(",")  #  type: ignore  # pylint: disable=E1101
        ]
        tables: list[str] = []
        indicators: list[tuple[str, str]] = []
        dataflows_seen: set[str] = set()

        for sym in symbols:
            if "::" not in sym:
                raise ValueError(
                    f"Invalid symbol format '{sym}'. Expected 'dataflow::identifier'. "
                    "Use `available_indicators()` or `list_tables()` to find valid symbols."
                )

            parts = sym.split("::", 1)
            dataflow = parts[0].strip().upper()
            identifier = parts[1].strip()

            if not identifier:
                raise ValueError(
                    f"Invalid symbol format '{sym}'. Identifier cannot be empty. "
                    "Expected 'dataflow::identifier'."
                )

            dataflows_seen.add(dataflow)
            # Tables can start with H_ or be any valid hierarchy ID for the dataflow
            is_table = False

            if identifier.startswith("H_"):
                is_table = True
            else:
                metadata = ImfMetadata()
                try:
                    hierarchies = metadata.get_dataflow_hierarchies(dataflow)
                    hierarchy_ids = {h.get("id") for h in hierarchies}
                    if identifier in hierarchy_ids:
                        is_table = True
                except Exception:  # noqa
                    pass  # If we can't check, assume it's an indicator

            if is_table:
                tables.append(sym)
            else:
                indicators.append((dataflow, identifier))

        if tables and indicators:
            raise ValueError(
                "Cannot mix tables and indicators in the same request. "
                f"Got tables: {tables} and indicators: {[f'{d}::{c}' for d, c in indicators]}"
            )

        if len(tables) > 1:
            raise ValueError(
                f"Only one table can be requested at a time. Got: {tables}"
            )

        if tables:
            self._is_table = True
            parts = tables[0].split("::", 1)
            self._dataflow = parts[0].upper()
            self._table_id = parts[1]
        else:
            self._is_table = False
            indicators_by_df: dict[str, list[str]] = {}

            for dataflow, code in indicators:
                if dataflow not in indicators_by_df:
                    indicators_by_df[dataflow] = []

                indicators_by_df[dataflow].append(code)

            self._indicators_by_dataflow = indicators_by_df

            if len(dataflows_seen) == 1:
                self._dataflow = list(dataflows_seen)[0]
                self._indicator_codes = [code for _, code in indicators]
            else:
                self._dataflow = None  # Multiple dataflows
                self._indicator_codes = []

            # Validate country, frequency, and transform using constraints API
            self._validate_indicator_params()

        return self