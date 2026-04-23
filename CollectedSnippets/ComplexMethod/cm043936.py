def get_dataflow_hierarchies(self, dataflow_id: str) -> list[dict]:
        """
        Get all hierarchies (presentation tables) available for a dataflow.

        This supports two types of presentations:
        1. Hierarchies from hierarchy.json (45 codelists)
        2. Presentations embedded in dataflow metadata (31 dataflows)

        Parameters
        ----------
        dataflow_id : str
            The dataflow ID (e.g., "FSIBSIS", "BOP_AGG", "IRFCL")

        Returns
        -------
        list[dict]
            List of hierarchy/presentation metadata dicts.
        """
        if dataflow_id not in self.dataflows:
            raise ValueError(f"Dataflow '{dataflow_id}' not found.")

        dataflow_obj = self.dataflows[dataflow_id]
        result = []

        # First, check for hierarchies from hierarchy.json (these have actual structure)
        dsd_id = dataflow_obj.get("structureRef", {}).get("id")

        if dsd_id and dsd_id in self.datastructures:
            dsd = self.datastructures[dsd_id]
            dimensions = dsd.get("dimensions", [])

            indicator_codelist_id = None
            # Priority-ordered list of dimension names to check for indicators
            indicator_candidates = [
                "INDICATOR",
                "COICOP_1999",
                "PRODUCTION_INDEX",
                "ACTIVITY",
                "PRODUCT",
                "SERIES",
                "ITEM",
                "ACCOUNTING_ENTRY",
                "SECTOR",
            ]

            dim_lookup = {d.get("id", ""): d for d in dimensions}
            # Check candidates in priority order (not dimension order)
            for candidate in indicator_candidates:
                if candidate in dim_lookup:
                    dim = dim_lookup[candidate]
                    indicator_codelist_id = self._resolve_codelist_id(
                        dataflow_id, dsd_id, candidate, dim
                    )
                    if indicator_codelist_id:
                        # Check if this codelist actually has hierarchies
                        if self._codelist_to_hierarchies_map.get(indicator_codelist_id):
                            break
                        # If no hierarchies, continue to next candidate
                        indicator_codelist_id = None

            # Fallback: check for any dimension with "INDICATOR" in its name
            if not indicator_codelist_id:
                for dim in dimensions:
                    dim_id = dim.get("id", "")
                    if "INDICATOR" in dim_id and dim_id not in indicator_candidates:
                        indicator_codelist_id = self._resolve_codelist_id(
                            dataflow_id, dsd_id, dim_id, dim
                        )
                        if indicator_codelist_id:
                            break

            if indicator_codelist_id:
                hierarchy_ids = self._codelist_to_hierarchies_map.get(
                    indicator_codelist_id, []
                )
                # Get available indicator values for this dataflow to filter hierarchies
                available_indicator_values: set[str] = set()

                try:
                    params = self.get_dataflow_parameters(dataflow_id)

                    if "INDICATOR" in params:
                        available_indicator_values.update(
                            opt.get("value", "") for opt in params["INDICATOR"]
                        )
                except Exception:  # noqa: S110
                    pass  # If we can't get parameters, include all hierarchies

                for hier_id in hierarchy_ids:
                    hier_obj = self.hierarchies.get(hier_id)
                    hier_code_values: set[str] = set()
                    if hier_obj:
                        # If we have available values, check if this hierarchy is compatible
                        if available_indicator_values:
                            hier_codes_raw = hier_obj.get("hierarchicalCodes", [])

                            def _extract_codes(codes_list):
                                for c in codes_list:
                                    # Extract actual code from URN like:
                                    # urn:sdmx:...CL_BOP_INDICATOR(10.0+.0).NIIP_AFR
                                    code_urn = c.get("code", "")
                                    # Only extract codes from INDICATOR codelists
                                    if (
                                        code_urn
                                        and "INDICATOR" in code_urn
                                        and "." in code_urn
                                    ):
                                        actual_code = code_urn.rsplit(".", 1)[-1]
                                        if actual_code:
                                            hier_code_values.add(  # pylint: disable=W0640
                                                actual_code
                                            )
                                    # Recurse into nested codes
                                    nested = c.get("hierarchicalCodes", [])
                                    if nested:
                                        _extract_codes(nested)  # pylint: disable=W0640

                            _extract_codes(hier_codes_raw)

                            # Check if ANY of the hierarchy's codes exist in the dataflow
                            # Use prefix matching since dataflow codes may have unit suffixes
                            # e.g., hierarchy code "FSI687_TREGK" should match "FSI687_TREGK_USD"
                            if hier_code_values:
                                has_match = False
                                # First try exact match (fast path)
                                if hier_code_values & available_indicator_values:
                                    has_match = True
                                else:
                                    # Prefix matching: check if any available indicator
                                    # starts with any hierarchy code
                                    for hier_code in hier_code_values:
                                        for avail_code in available_indicator_values:
                                            if avail_code.startswith(hier_code):
                                                has_match = True
                                                break
                                        if has_match:
                                            break
                                if not has_match:
                                    # No overlap - skip this hierarchy for this dataflow
                                    continue

                        # Check if hierarchy has multiple top-level codes
                        top_level_codes = hier_obj.get("hierarchicalCodes", [])

                        if len(top_level_codes) > 1 and dataflow_id == "IRFCL":
                            # Split into separate tables - one per top-level code
                            for idx, top_code in enumerate(top_level_codes):
                                top_code_id = top_code.get("id", "")
                                top_code_urn = top_code.get("code", "")
                                # Extract actual code from URN
                                actual_code = (
                                    top_code_urn.rsplit(".", 1)[-1]
                                    if "." in top_code_urn
                                    else top_code_id
                                )
                                # Get label from the codelist specified in the URN
                                urn_codelist_id = self._parse_codelist_id_from_urn(
                                    top_code_urn
                                )
                                table_label = self._codelist_cache.get(
                                    urn_codelist_id or indicator_codelist_id, {}
                                ).get(actual_code, actual_code)
                                # Check for SECTION codelist for better labels
                                section_codelist_id = f"CL_{dataflow_id}_SECTION"
                                section_codes = self._codelist_cache.get(
                                    section_codelist_id, {}
                                )
                                # Match section by prefix in actual_code
                                for (
                                    section_code,
                                    section_label,
                                ) in section_codes.items():
                                    if actual_code.startswith(section_code):
                                        table_label = section_label
                                        break

                                result.append(
                                    {
                                        "id": f"{hier_id}:{top_code_id}",
                                        "name": table_label,
                                        "description": "",
                                        "codelist_id": indicator_codelist_id,
                                        "agency_id": hier_obj.get("agencyID", ""),
                                        "version": hier_obj.get("version", ""),
                                        "type": "hierarchy",
                                        "table_index": idx,
                                        "top_level_code_id": top_code_id,
                                        "indicator_code": actual_code,
                                    }
                                )
                        else:
                            # Single top-level code - return as single table
                            name = hier_obj.get("name", "")
                            descriptions = hier_obj.get("descriptions", {})
                            desc = descriptions.get("en", "") if descriptions else ""
                            result.append(
                                {
                                    "id": hier_id,
                                    "name": name,
                                    "description": desc,
                                    "codelist_id": indicator_codelist_id,
                                    "agency_id": hier_obj.get("agencyID", ""),
                                    "version": hier_obj.get("version", ""),
                                    "type": "hierarchy",
                                }
                            )

        return result