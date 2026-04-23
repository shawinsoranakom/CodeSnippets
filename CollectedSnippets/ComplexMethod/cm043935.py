def _get_dimension_for_codelist(
        self, dataflow_id: str, codelist_id: str
    ) -> str | None:
        """
        Find which dimension uses the given codelist ID.

        Parameters
        ----------
        dataflow_id : str
            The dataflow ID
        codelist_id : str
            The codelist ID (e.g., "CL_BOP_INDICATOR")

        Returns
        -------
        str | None
            The dimension ID that uses this codelist, or None if not found.
        """
        if dataflow_id not in self.dataflows:
            return None

        df_obj = self.dataflows[dataflow_id]
        dsd_id = df_obj.get("structureRef", {}).get("id")
        if not dsd_id or dsd_id not in self.datastructures:
            return None

        dsd = self.datastructures[dsd_id]
        dimensions = dsd.get("dimensions", [])

        # First pass: exact match
        for dim in dimensions:
            dim_id = dim.get("id")
            if not dim_id:
                continue

            # Resolve the codelist for this dimension
            resolved_codelist = self._resolve_codelist_id(
                dataflow_id, dsd_id, dim_id, dim
            )
            if resolved_codelist == codelist_id:
                return dim_id

        # Second pass: fuzzy match by dimension name appearing anywhere in codelist ID
        # e.g., CL_IRFCL_DEFAULT_INDICATOR_PUB2 should match INDICATOR dimension
        # Split codelist into segments and check if any segment matches a dimension
        codelist_segments = set(seg.upper() for seg in codelist_id.split("_"))
        for dim in dimensions:
            dim_id = dim.get("id")
            if dim_id and dim_id.upper() in codelist_segments:
                return dim_id

        # Third pass: check if dimension name is a substring of codelist ID
        # Handles cases like CL_IRFCL_DEFAULT_INDICATOR_PUB2 -> INDICATOR
        codelist_upper = codelist_id.upper()
        for dim in dimensions:
            dim_id = dim.get("id")
            if dim_id and dim_id.upper() in codelist_upper:
                return dim_id

        return None