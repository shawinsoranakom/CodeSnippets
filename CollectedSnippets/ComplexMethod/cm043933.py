def get_indicators_in(self, dataflow_id: str) -> list:
        """Get indicators available in a given dataflow."""
        if dataflow_id not in self.dataflows:
            raise ValueError(f"Dataflow '{dataflow_id}' not found.")

        dataflow_obj = self.dataflows[dataflow_id]
        dataflow_name = dataflow_obj.get("name", "").replace("\\xa0", "").strip()
        structure_ref = dataflow_obj.get("structureRef", {})
        structure_id = structure_ref.get("id", "")
        agency_id = dataflow_obj.get("agencyID", structure_ref.get("agencyID", "IMF"))
        dsd_id = structure_ref.get("id", "")

        if not dsd_id or dsd_id not in self.datastructures:
            raise ValueError(f"Data structure not found for dataflow '{dataflow_id}'.")

        dsd = self.datastructures[dsd_id]
        all_dims = dsd.get("dimensions", [])

        # Get valid codes from parameters API
        try:
            params = self.get_dataflow_parameters(dataflow_id)
        except Exception:  # noqa: BLE001
            params = {}

        full_indicator_list = []

        indicator_id_candidates = [
            "INDICATOR",
            "PRODUCTION_INDEX",
            "COICOP_1999",
            "INDEX_TYPE",
            "ACTIVITY",
            "PRODUCT",
            "SERIES",
            "ITEM",
            "BOP_ACCOUNTING_ENTRY",
            "ACCOUNTING_ENTRY",
        ]

        for dim in all_dims:
            dim_id = dim.get("id")

            is_indicator_candidate = dim_id in indicator_id_candidates
            if not is_indicator_candidate and any(
                keyword in dim_id
                for keyword in ["INDICATOR", "ACCOUNTING_ENTRY", "ENTRY"]
            ):
                is_indicator_candidate = True

            if not is_indicator_candidate:
                continue

            # Get valid codes with labels from parameters API
            dim_params = params.get(dim_id, [])
            if not dim_params:
                continue

            # Resolve codelist ID for this dimension to look up descriptions
            codelist_id = self._resolve_codelist_id(dataflow_id, dsd_id, dim_id, dim)
            descriptions_map: dict = {}
            if codelist_id:
                # Try to get cached descriptions
                descriptions_map = self._codelist_descriptions.get(codelist_id, {})
                # If not cached, try to load the codelist to populate descriptions
                if not descriptions_map and codelist_id not in self._codelist_cache:
                    try:
                        self._get_codelist_map(codelist_id, agency_id, dataflow_id)
                        descriptions_map = self._codelist_descriptions.get(
                            codelist_id, {}
                        )
                    except Exception:  # noqa
                        pass  # Codelist not available, continue without descriptions

            # Parameters API already provides labels - use them directly
            for param in dim_params:
                code_id = param["value"]
                code_label = param.get("label", code_id)
                series_id = f"{dataflow_id}::{code_id}"

                # Look up description from codelist, fall back to label if not found
                description = descriptions_map.get(code_id, "")

                indicator_entry = {
                    "dataflow_id": dataflow_id,
                    "dataflow_name": dataflow_name,
                    "structure_id": structure_id,
                    "agency_id": agency_id,
                    "dimension_id": dim_id,
                    "indicator": code_id,
                    "label": code_label,
                    "description": description,
                    "series_id": series_id,
                }
                full_indicator_list.append(indicator_entry)

        # Check for activity-related codelists
        dim_ids = {d.get("id") for d in all_dims if d.get("id")}
        if "ACTIVITY" in dim_ids:
            activity_codelist_id = f"CL_{dataflow_id}_ACTIVITY"
            if activity_codelist_id in self._codelist_cache:
                codes_map = self._get_codelist_map(
                    activity_codelist_id, agency_id, dataflow_id
                )
                descriptions_map = self._codelist_descriptions.get(
                    activity_codelist_id, {}
                )
                for code_id, code_name in codes_map.items():
                    series_id = f"{dataflow_id}::{code_id}"
                    entry = {
                        "dataflow_id": dataflow_id,
                        "dataflow_name": dataflow_name,
                        "structure_id": structure_id,
                        "agency_id": agency_id,
                        "dimension_id": "ACTIVITY",
                        "indicator": code_id,
                        "label": code_name,
                        "description": descriptions_map.get(code_id, ""),
                        "series_id": series_id,
                    }
                    full_indicator_list.append(entry)

        if not full_indicator_list:
            raise KeyError(
                f"Could not find an indicator-like dimension for dataflow '{dataflow_id}'."
            )

        return full_indicator_list