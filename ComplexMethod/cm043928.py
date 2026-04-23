def get_dataflow_parameters(self, dataflow_id: str) -> dict[str, list[dict]]:
        """Get available parameters for a given dataflow."""
        if dataflow_id not in self.dataflows:
            raise ValueError(f"Dataflow '{dataflow_id}' not found.")

        if (
            hasattr(self, "_dataflow_parameters_cache")
            and dataflow_id in self._dataflow_parameters_cache
        ):
            return self._dataflow_parameters_cache[dataflow_id]

        df_obj = self.dataflows[dataflow_id]
        agency_id = df_obj.get("agencyID")
        dsd_id = df_obj.get("structureRef", {}).get("id")
        dsd = self.datastructures.get(dsd_id, {})
        if not dsd:
            return {}

        dimensions_metadata = {
            dim["id"]: dim for dim in dsd.get("dimensions", []) if dim.get("id")
        }

        constraints_response = self.get_available_constraints(
            dataflow_id=dataflow_id,
            key="all",
            component_id="all",
            mode="available",
            references="all",
        )
        key_values = constraints_response.get("key_values", [])
        constrained_values_map = {kv["id"]: kv.get("values", []) for kv in key_values}

        parameters: dict[str, list[dict]] = {}
        dimension_codes_cache: dict[str, dict] = {}

        def _get_codes(dim_id: str) -> dict:
            if dim_id in dimension_codes_cache:
                return dimension_codes_cache[dim_id]

            dim_meta = dimensions_metadata.get(dim_id, {})
            codelist_id = self._resolve_codelist_id(
                dataflow_id, dsd_id, dim_id, dim_meta
            )
            if codelist_id:
                codes = (
                    self._get_codelist_map(
                        codelist_id, agency_id, dataflow_id, include_descriptions=False
                    )
                    or {}
                )
                dimension_codes_cache[dim_id] = codes
                return codes
            return {}

        for dim_id in dimensions_metadata:
            if dim_id == "TIME_PERIOD":
                continue

            # Get the codelist ID for this dimension upfront
            dim_meta = dimensions_metadata.get(dim_id, {})
            codelist_id = self._resolve_codelist_id(
                dataflow_id, dsd_id, dim_id, dim_meta
            )

            if not codelist_id:
                continue

            # Get the full codelist from cache
            full_codes = self._codelist_cache.get(codelist_id, {})
            if not full_codes:
                # Try to fetch it if not in cache
                codes_map = _get_codes(dim_id)
                if not codes_map:
                    continue
                full_codes = codes_map

            value_ids_to_use = (
                constrained_values_map[dim_id]
                if dim_id in constrained_values_map
                else list(full_codes.keys())
            )

            options: list = []
            for val_id in value_ids_to_use:
                # Look up the label from the full codes
                label = full_codes.get(val_id, val_id)

                # If it's a dict (from _get_codes with descriptions), extract the name
                if isinstance(label, dict):
                    label = label.get("name", val_id)

                # Ensure we have a string label
                if not label or label == val_id:
                    # If still no proper label, use the code itself
                    label = val_id

                options.append({"label": label, "value": val_id.strip()})

            if options:
                parameters[dim_id] = options

        time_period_options, _ = self._build_time_period_parameters(
            constraints_response
        )
        if time_period_options:
            parameters["TIME_PERIOD"] = time_period_options

        if hasattr(self, "_dataflow_parameters_cache"):
            self._dataflow_parameters_cache[dataflow_id] = parameters

        return parameters