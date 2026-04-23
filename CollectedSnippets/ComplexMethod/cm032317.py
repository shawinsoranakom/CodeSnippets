def insert(self, documents: list[dict], index_name: str, memory_id: str = None) -> list[str]:
        # Refers to https://www.elastic.co/guide/en/elasticsearch/reference/current/docs-bulk.html
        operations = []
        for d in documents:
            assert "_id" not in d
            assert "id" in d
            d_copy_raw = copy.deepcopy(d)
            d_copy = self.map_message_to_es_fields(d_copy_raw)
            d_copy["memory_id"] = memory_id
            meta_id = d_copy.pop("id", "")
            operations.append(
                {"index": {"_index": index_name, "_id": meta_id}})
            operations.append(d_copy)
        res = []
        for _ in range(ATTEMPT_TIME):
            try:
                res = []
                r = self.es.bulk(index=index_name, operations=operations,
                                 refresh=False, timeout="60s")
                if re.search(r"False", str(r["errors"]), re.IGNORECASE):
                    return res

                for item in r["items"]:
                    for action in ["create", "delete", "index", "update"]:
                        if action in item and "error" in item[action]:
                            res.append(str(item[action]["_id"]) + ":" + str(item[action]["error"]))
                return res
            except ConnectionTimeout:
                self.logger.exception("ES request timeout")
                time.sleep(3)
                self._connect()
                continue
            except Exception as e:
                res.append(str(e))
                self.logger.warning("ESConnection.insert got exception: " + str(e))

        return res