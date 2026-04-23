def _coerce_filter_clauses(self, filter_obj: dict | None) -> list[dict]:
        """Convert filter expressions into OpenSearch-compatible filter clauses.

        This method accepts two filter formats and converts them to standardized
        OpenSearch query clauses:

        Format A - Explicit filters:
        {"filter": [{"term": {"field": "value"}}, {"terms": {"field": ["val1", "val2"]}}],
         "limit": 10, "score_threshold": 1.5}

        Format B - Context-style mapping:
        {"data_sources": ["file1.pdf"], "document_types": ["pdf"], "owners": ["user1"]}

        Args:
            filter_obj: Filter configuration dictionary or None

        Returns:
            List of OpenSearch filter clauses (term/terms objects)
            Placeholder values with "__IMPOSSIBLE_VALUE__" are ignored
        """
        if not filter_obj:
            return []

        # If it is a string, try to parse it once
        if isinstance(filter_obj, str):
            try:
                filter_obj = json.loads(filter_obj)
            except json.JSONDecodeError:
                # Not valid JSON - treat as no filters
                return []

        # Case A: already an explicit list/dict under "filter"
        if "filter" in filter_obj:
            raw = filter_obj["filter"]
            if isinstance(raw, dict):
                raw = [raw]
            explicit_clauses: list[dict] = []
            for f in raw or []:
                if "term" in f and isinstance(f["term"], dict) and not self._is_placeholder_term(f["term"]):
                    explicit_clauses.append(f)
                elif "terms" in f and isinstance(f["terms"], dict):
                    field, vals = next(iter(f["terms"].items()))
                    if isinstance(vals, list) and len(vals) > 0:
                        explicit_clauses.append(f)
            return explicit_clauses

        # Case B: convert context-style maps into clauses
        field_mapping = {
            "data_sources": "filename",
            "document_types": "mimetype",
            "owners": "owner",
        }
        context_clauses: list[dict] = []
        for k, values in filter_obj.items():
            if not isinstance(values, list):
                continue
            field = field_mapping.get(k, k)
            if len(values) == 0:
                # Match-nothing placeholder (kept to mirror your tool semantics)
                context_clauses.append({"term": {field: "__IMPOSSIBLE_VALUE__"}})
            elif len(values) == 1:
                if values[0] != "__IMPOSSIBLE_VALUE__":
                    context_clauses.append({"term": {field: values[0]}})
            else:
                context_clauses.append({"terms": {field: values}})
        return context_clauses