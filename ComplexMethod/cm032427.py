def build_delete_query(self, condition: dict, knowledgebase_id: str) -> dict:
        """
        Simulates the query construction logic from es_conn.py/opensearch_conn.py delete method.
        This is extracted to test the logic without needing actual ES/OS connections.
        """
        condition = condition.copy()  # Don't mutate the original
        condition["kb_id"] = knowledgebase_id

        # Build a bool query that combines id filter with other conditions
        bool_query = Q("bool")

        # Handle chunk IDs if present
        if "id" in condition:
            chunk_ids = condition["id"]
            if not isinstance(chunk_ids, list):
                chunk_ids = [chunk_ids]
            if chunk_ids:
                # Filter by specific chunk IDs
                bool_query.filter.append(Q("ids", values=chunk_ids))

        # Add all other conditions as filters
        for k, v in condition.items():
            if k == "id":
                continue  # Already handled above
            if k == "exists":
                bool_query.filter.append(Q("exists", field=v))
            elif k == "must_not":
                if isinstance(v, dict):
                    for kk, vv in v.items():
                        if kk == "exists":
                            bool_query.must_not.append(Q("exists", field=vv))
            elif isinstance(v, list):
                bool_query.must.append(Q("terms", **{k: v}))
            elif isinstance(v, str) or isinstance(v, int):
                bool_query.must.append(Q("term", **{k: v}))
            elif v is not None:
                raise Exception("Condition value must be int, str or list.")

        # If no filters were added, use match_all
        if not bool_query.filter and not bool_query.must and not bool_query.must_not:
            qry = Q("match_all")
        else:
            qry = bool_query

        return Search().query(qry).to_dict()