def _resolve_codelist_id(
        self, dataflow_id: str, dsd_id: str | None, dim_id: str, dim_meta: dict
    ) -> str | None:
        if not dim_id:
            return None

        # Check for explicit codelist reference first
        representation = dim_meta.get("representation", {})
        codelist_ref = representation.get("codelist")
        if isinstance(codelist_ref, dict):
            return codelist_ref.get("id")
        if isinstance(codelist_ref, str):
            return codelist_ref

        candidates: list[str] = []
        seen = set()

        def add_candidate(candidate: str):
            if candidate and candidate not in seen:
                candidates.append(candidate)
                seen.add(candidate)

        concept_ref = dim_meta.get("conceptRef") or {}
        concept_id = concept_ref.get("id")

        # For country-like dimensions (JURISDICTION, REF_AREA, COUNTRY, etc.),
        # prioritize dataflow-specific ISO country codelists first.
        country_dims = {"JURISDICTION", "REF_AREA", "COUNTRY", "AREA"}
        is_country_dim = dim_id.upper() in country_dims or (
            concept_id and concept_id.upper() in {"COUNTRY", "REF_AREA"}
        )

        if is_country_dim and dataflow_id:
            # Try dataflow-specific ISO country codelist first
            base_dataflow = dataflow_id.split("_")[0]
            add_candidate(f"CL_{base_dataflow}_ISO_COUNTRY")
            add_candidate(f"CL_{dataflow_id}_COUNTRY")
            add_candidate(f"CL_{base_dataflow}_COUNTRY")

        # Priority 1: Dataflow-specific patterns (most specific first)
        if dataflow_id:
            add_candidate(f"CL_{dataflow_id}_{dim_id}")
            add_candidate(f"CL_{dataflow_id}_{dim_id}_PUB")  # _PUB suffix variant
            if "COUNTRY" in dim_id:
                add_candidate(f"CL_{dataflow_id}_COUNTRY")
                add_candidate(f"CL_{dataflow_id}_COUNTRY_PUB")
            if "_" in dataflow_id:
                base_dataflow = dataflow_id.split("_")[0]
                add_candidate(f"CL_{base_dataflow}_{dim_id}")
                add_candidate(f"CL_{base_dataflow}_{dim_id}_PUB")

        # Priority 2: DSD patterns
        if dsd_id:
            dsd_base = dsd_id.replace("DSD_", "")
            add_candidate(f"CL_{dsd_base}_{dim_id}")

        # Priority 3: Parent scheme patterns
        parent_scheme_id = concept_ref.get("maintainableParentID")
        if parent_scheme_id:
            scheme_base = parent_scheme_id.replace("CS_", "CL_", 1)
            add_candidate(f"{scheme_base}_{dim_id}")
            add_candidate(scheme_base)

        # Priority 4: Direct/generic matches (fallback)
        add_candidate(f"CL_{dim_id}")
        if concept_id:
            add_candidate(f"CL_{concept_id}")

        # Check cache for exact matches first
        for candidate in candidates:
            if candidate in self._codelist_cache:
                return candidate

        # Case-insensitive fallback for dataflow-specific codelists
        # IMF has inconsistent casing (e.g., CL_LS_TYPE_OF_TRANSFORMAtION)
        cache_keys_upper = {k.upper(): k for k in self._codelist_cache}
        for candidate in candidates:
            actual_key = cache_keys_upper.get(candidate.upper())
            if actual_key:
                return actual_key

        # Consolidated mapping for common variations
        # This combines the old variations dict and generic_dimensions list
        common_mappings = {
            # Geographic dimensions
            (
                "REF_AREA",
                "AREA",
                "COUNTRY",
                "JURISDICTION",
                "GEOGRAPHICAL_AREA",
            ): "AREA",
            ("COUNTERPART_COUNTRY",): "COUNTRY",
            # Statistical dimensions
            ("COMPOSITE_BREAKDOWN", "COMP_BREAKDOWN"): "COMPOSITE_BREAKDOWN",
            ("DISABILITY_STATUS", "DISABILITY"): "DISABILITY",
            ("INCOME_WEALTH_QUANTILE", "QUANTILE"): "QUANTILE",
            ("TYPE_OF_TRANSFORMATION", "TRANSFORMATION"): "TRANSFORMATION",
            ("WGT_TYPE", "WEIGHT_TYPE", "CTOT_WEIGHT_TYPE"): "WEIGHT_TYPE",
            ("INDICATOR", "INDICATORS"): "INDICATOR",
            ("UNIT", "UNIT_MEASURE", "UNIT_MULT"): "UNIT",
        }

        # Check if dimension matches any common pattern
        for patterns, base_name in common_mappings.items():
            if any(pattern in dim_id.upper() for pattern in patterns):
                # Try generic first
                generic_cl = f"CL_{base_name}"
                if generic_cl in self._codelist_cache:
                    return generic_cl
                # Then try dataflow-specific
                specific_cl = f"CL_{dataflow_id}_{base_name}"
                if specific_cl in self._codelist_cache:
                    return specific_cl

        # Special handling for counterpart dimensions
        if "COUNTERPART_" in dim_id:
            base_dim_id = dim_id.replace("COUNTERPART_", "")
            if dsd_id and dsd_id in self.datastructures:
                dsd = self.datastructures[dsd_id]
                for d in dsd.get("dimensions", []):
                    if d.get("id") == base_dim_id:
                        return self._resolve_codelist_id(
                            dataflow_id, dsd_id, base_dim_id, d
                        )

        # Activity/Product fallbacks
        if "ACTIVITY" in dim_id.upper() or "PRODUCTION_INDEX" in dim_id.upper():
            activity_candidates = [
                "CL_PPI_ACTIVITY",
                "CL_MCDREO_ACTIVITY",
                "CL_ACTIVITY_ISIC4",
                "CL_NEA_ACTIVITY",
                "CL_ACTIVITY",
            ]
            for candidate in activity_candidates:
                if candidate in self._codelist_cache:
                    return candidate

        if "COICOP" in dim_id.upper():
            coicop_candidates = ["CL_COICOP_1999", "CL_COICOP_2018"]
            for candidate in coicop_candidates:
                if candidate in self._codelist_cache:
                    return candidate

        # Fuzzy matching as last resort
        dim_upper = dim_id.upper()

        # Try exact substring match
        for cache_key in self._codelist_cache:
            if cache_key.startswith("CL_MASTER"):
                continue
            if dim_upper in cache_key.upper():
                return cache_key

        # Try matching significant parts
        dim_parts = [p for p in dim_id.split("_") if len(p) > 2]
        if len(dim_parts) > 1:
            for cache_key in self._codelist_cache:
                if cache_key.startswith("CL_MASTER"):
                    continue
                cache_key_upper = cache_key.upper()
                if all(part.upper() in cache_key_upper for part in dim_parts):
                    return cache_key

        # Return first candidate or None
        return candidates[0] if candidates else None