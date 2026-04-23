def _validate_indicator_params(self):
        """Validate country, frequency, and transform using the constraints API."""
        # pylint: disable=import-outside-toplevel
        from openbb_imf.utils.metadata import ImfMetadata

        metadata = ImfMetadata()

        def build_key_up_to(target_dim: str) -> str:
            """Build constraint key up to (and including) target dimension."""
            key_parts: list[str] = []
            countries = self.country.split(",") if self.country else []  # type: ignore  # pylint: disable=E1101
            countries_str = (
                "*"
                if countries in ["*", "all"]
                else "+".join([c.upper() for c in countries])
            )

            for dim_id in dim_order:
                if dim_id == target_dim:
                    key_parts.append("*")
                    break
                if dim_id == country_dim:
                    key_parts.append(countries_str if countries_str else "*")
                elif dim_id == indicator_dim:
                    # Use all indicator codes for this dataflow
                    key_parts.append(
                        "+".join(indicator_codes) if indicator_codes else "*"
                    )
                elif dim_id == freq_dim:
                    freq_map = {
                        "annual": "A",
                        "quarter": "Q",
                        "month": "M",
                        "day": "D",
                    }
                    freq_val = freq_map.get(str(self.frequency).lower(), self.frequency)
                    key_parts.append(str(freq_val) if self.frequency else "*")
                elif dim_id == transform_dim:
                    key_parts.append(str(self.transform) if self.transform else "*")
                else:
                    key_parts.append("*")
            return ".".join(key_parts)

        def get_available_values(dim_id: str, dataflow_id: str) -> list[str]:
            """Get available values for a dimension using constraints API."""
            key = build_key_up_to(dim_id)
            constraints = metadata.get_available_constraints(
                dataflow_id=dataflow_id,
                key=key,
                component_id=dim_id,
            )
            for kv in constraints.get("key_values", []):
                if kv.get("id") == dim_id:
                    return kv.get("values", [])
            return []

        # For each dataflow, validate the parameters
        for dataflow_id, indicator_codes in self._indicators_by_dataflow.items():
            df_obj = metadata.dataflows.get(dataflow_id, {})

            if not df_obj:
                continue

            dsd_id = df_obj.get("structureRef", {}).get("id")
            dsd = metadata.datastructures.get(dsd_id, {})
            dimensions = dsd.get("dimensions", [])
            sorted_dims = sorted(
                [d for d in dimensions if d.get("id") != "TIME_PERIOD"],
                key=lambda x: int(x.get("position", 0)),
            )
            dim_order = [d["id"] for d in sorted_dims]
            country_dim = (
                "COUNTRY"
                if "COUNTRY" in dim_order
                else "JURISDICTION" if "JURISDICTION" in dim_order else "REF_AREA"
            )
            freq_dim = "FREQUENCY" if "FREQUENCY" in dim_order else "FREQ"

            transform_dim, _, _, _ = detect_transform_dimension(dataflow_id)
            indicator_dim_candidates = [
                "INDICATOR",
                "COICOP_1999",
                "SERIES",
                "ITEM",
                "BOP_ACCOUNTING_ENTRY",
                "ACTIVITY",
            ]
            indicator_dim = next(
                (d for d in indicator_dim_candidates if d in dim_order), None
            )

            # Validate country
            if self.country and country_dim in dim_order:
                available_countries = get_available_values(country_dim, dataflow_id)
                if available_countries:
                    countries = [c.strip().upper() for c in self.country.split(",")]  # type: ignore  # pylint: disable=E1101
                    invalid = [
                        c
                        for c in countries
                        if c not in available_countries and c not in ("*", "all")
                    ]
                    if invalid:
                        raise ValueError(
                            f"Invalid value(s) for dimension 'country': {invalid}. "
                            + f"Given prior selections {{'indicator': '{','.join(indicator_codes)}'}}, "
                            + f"available values are: {sorted(available_countries)}"
                        )

            if (
                self.frequency
                and self.frequency.lower() not in ("all", "*")  # type: ignore  # pylint: disable=E1101
                and freq_dim in dim_order
            ):
                freq_map = {"annual": "A", "quarter": "Q", "month": "M", "day": "D"}
                freq_val = freq_map.get(str(self.frequency).lower(), self.frequency)
                available_freqs = get_available_values(freq_dim, dataflow_id)
                if available_freqs and freq_val not in available_freqs:
                    indicator_str = ",".join(indicator_codes)
                    raise ValueError(
                        f"Invalid value(s) for dimension 'frequency': ['{freq_val}']. "
                        f"Given prior selections {{'country': '{self.country}', "
                        f"'indicator': '{indicator_str}'}}, "
                        f"available values are: {available_freqs}"
                    )

            # Validate transform (skip if 'all' or '*')
            if (
                self.transform
                and self.transform.lower() not in ("all", "*")  # type: ignore  # pylint: disable=E1101
                and transform_dim
                and transform_dim in dim_order
            ):
                _, _, transform_lookup, unit_lookup = detect_transform_dimension(
                    dataflow_id
                )
                # Resolve user-friendly name to code
                transform_val = self.transform.strip().lower()  # type: ignore  # pylint: disable=E1101
                resolved_code = transform_lookup.get(
                    transform_val, unit_lookup.get(transform_val, self.transform)
                )
                available_transforms = get_available_values(transform_dim, dataflow_id)

                if available_transforms and resolved_code not in available_transforms:
                    indicator_str = ",".join(indicator_codes)
                    raise ValueError(
                        f"Invalid value(s) for dimension 'transform': ['{resolved_code}']. "
                        f"Given prior selections {{'country': '{self.country}', "
                        f"'indicator': '{indicator_str}'}}, "
                        f"available values are: {available_transforms}"
                    )