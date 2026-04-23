def _get_codelist_map(
        self,
        codelist_id: str,
        agency_id: str,
        dataflow_id: str,
        include_descriptions: bool = False,
    ) -> dict:
        """Download and cache the codelist map for a given codelist ID."""
        with self._codelist_lock:
            if codelist_id in self._codelist_cache:
                if include_descriptions and codelist_id in self._codelist_descriptions:
                    result = {}
                    for code_id, code_name in self._codelist_cache[codelist_id].items():
                        result[code_id] = {
                            "name": code_name,
                            "description": self._codelist_descriptions[codelist_id].get(
                                code_id, ""
                            ),
                        }
                    return result
                return self._codelist_cache[codelist_id].copy()

        # If not in cache, try to bulk fetch and cache
        self._bulk_fetch_and_cache_codelists(agency_id, dataflow_id)

        # Try again from cache
        with self._codelist_lock:
            if codelist_id in self._codelist_cache:
                if include_descriptions and codelist_id in self._codelist_descriptions:
                    result = {}
                    for code_id, code_name in self._codelist_cache[codelist_id].items():
                        result[code_id] = {
                            "name": code_name,
                            "description": self._codelist_descriptions[codelist_id].get(
                                code_id, ""
                            ),
                        }
                    return result
                return self._codelist_cache[codelist_id].copy()

        warnings.warn(f"Codelist '{codelist_id}' not found.", OpenBBWarning)
        return {}