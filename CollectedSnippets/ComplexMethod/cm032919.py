def delete(self, condition: dict, indexName: str, knowledgebaseId: str) -> int:
        assert "_id" not in condition
        condition["kb_id"] = knowledgebaseId

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
            # If chunk_ids is empty, we don't add an ids filter - rely on other conditions

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

        # If no filters were added, use match_all (for tenant-wide operations)
        if not bool_query.filter and not bool_query.must and not bool_query.must_not:
            qry = Q("match_all")
        else:
            qry = bool_query
        logger.debug("OSConnection.delete query: " + json.dumps(qry.to_dict()))
        for _ in range(ATTEMPT_TIME):
            try:
                # print(Search().query(qry).to_dict(), flush=True)
                res = self.os.delete_by_query(
                    index=indexName,
                    body=Search().query(qry).to_dict(),
                    refresh=True)
                return res["deleted"]
            except Exception as e:
                logger.warning("OSConnection.delete got exception: " + str(e))
                if re.search(r"(timeout|connection)", str(e).lower()):
                    time.sleep(3)
                    continue
                if re.search(r"(not_found)", str(e), re.IGNORECASE):
                    return 0
        return 0