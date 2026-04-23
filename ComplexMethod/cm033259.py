def get_metadata_summary(cls, kb_id: str, doc_ids=None) -> Dict:
        """
        Get metadata summary for documents in a knowledge base.

        Args:
            kb_id: Knowledge base ID
            doc_ids: Optional list of document IDs to filter by

        Returns:
            Dictionary with metadata field statistics in format:
            {
                "field_name": {
                    "type": "string" | "number" | "list" | "time",
                    "values": [("value1", count1), ("value2", count2), ...]  # sorted by count desc
                }
            }
        """
        def _is_time_string(value: str) -> bool:
            """Check if a string value is an ISO 8601 datetime (e.g., '2026-02-03T00:00:00')."""
            if not isinstance(value, str):
                return False
            return bool(re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$', value))

        def _meta_value_type(value):
            """Determine the type of a metadata value."""
            if value is None:
                return None
            if isinstance(value, list):
                return "list"
            if isinstance(value, bool):
                return "string"
            if isinstance(value, (int, float)):
                return "number"
            if isinstance(value, str) and _is_time_string(value):
                return "time"
            return "string"

        try:
            condition = {"kb_id": kb_id}
            if doc_ids:
                condition["id"] = doc_ids
            results = cls._search_metadata(kb_id, condition=condition)
            if not results:
                return {}

            # Aggregate metadata
            summary = {}
            type_counter = {}

            logging.debug(f"[METADATA SUMMARY] KB: {kb_id}, doc_ids: {doc_ids}")

            # Use helper to iterate over results in any format
            for doc_id, doc in cls._iter_search_results(results):

                doc_meta = cls._extract_metadata(doc)

                for k, v in doc_meta.items():
                    # Track type counts for this field
                    value_type = _meta_value_type(v)
                    if value_type:
                        if k not in type_counter:
                            type_counter[k] = {}
                        type_counter[k][value_type] = type_counter[k].get(value_type, 0) + 1

                    # Aggregate value counts
                    values = v if isinstance(v, list) else [v]
                    for vv in values:
                        if vv is None:
                            continue
                        sv = str(vv)
                        if k not in summary:
                            summary[k] = {}
                        summary[k][sv] = summary[k].get(sv, 0) + 1

            # Build result with type information and sorted values
            result = {}
            for k, v in summary.items():
                values = sorted([(val, cnt) for val, cnt in v.items()], key=lambda x: x[1], reverse=True)
                type_counts = type_counter.get(k, {})
                value_type = "string"
                if type_counts:
                    value_type = max(type_counts.items(), key=lambda item: item[1])[0]
                result[k] = {"type": value_type, "values": values}

            logging.debug(f"[METADATA SUMMARY] Final result: {result}")
            return result

        except Exception as e:
            logging.error(f"Error getting metadata summary for KB {kb_id}: {e}")
            return {}