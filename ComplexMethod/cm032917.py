def insert(self, documents: list[dict], indexName: str, knowledgebaseId: str = None) -> list[str]:
        # Refers to https://opensearch.org/docs/latest/api-reference/document-apis/bulk/
        operations = []
        for d in documents:
            assert "_id" not in d
            assert "id" in d
            d_copy = copy.deepcopy(d)
            meta_id = d_copy.pop("id", "")
            operations.append(
                {"index": {"_index": indexName, "_id": meta_id}})
            operations.append(d_copy)

        res = []
        for _ in range(ATTEMPT_TIME):
            try:
                res = []
                r = self.os.bulk(index=(indexName), body=operations,
                                 refresh=False, timeout=60)
                if re.search(r"False", str(r["errors"]), re.IGNORECASE):
                    return res

                for item in r["items"]:
                    for action in ["create", "delete", "index", "update"]:
                        if action in item and "error" in item[action]:
                            res.append(str(item[action]["_id"]) + ":" + str(item[action]["error"]))
                return res
            except Exception as e:
                res.append(str(e))
                logger.warning("OSConnection.insert got exception: " + str(e))
                res = []
                if re.search(r"(Timeout|time out)", str(e), re.IGNORECASE):
                    res.append(str(e))
                    time.sleep(3)
                    continue
        return res