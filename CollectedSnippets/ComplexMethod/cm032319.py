def delete(self, condition: dict, index_name: str, memory_id: str) -> int:
        assert "_id" not in condition
        condition_dict = {self.convert_field_name(k): v for k, v in condition.items()}
        condition_dict["memory_id"] = memory_id
        if "id" in condition_dict:
            message_ids = condition_dict["id"]
            if not isinstance(message_ids, list):
                message_ids = [message_ids]
            if not message_ids:  # when message_ids is empty, delete all
                qry = Q("match_all")
            else:
                qry = Q("ids", values=message_ids)
        else:
            qry = Q("bool")
            for k, v in condition_dict.items():
                if k == "exists":
                    qry.filter.append(Q("exists", field=v))

                elif k == "must_not":
                    if isinstance(v, dict):
                        for kk, vv in v.items():
                            if kk == "exists":
                                qry.must_not.append(Q("exists", field=vv))

                elif isinstance(v, list):
                    qry.must.append(Q("terms", **{k: v}))
                elif isinstance(v, str) or isinstance(v, int):
                    qry.must.append(Q("term", **{k: v}))
                else:
                    raise Exception("Condition value must be int, str or list.")
        self.logger.debug("ESConnection.delete query: " + json.dumps(qry.to_dict()))
        for _ in range(ATTEMPT_TIME):
            try:
                res = self.es.delete_by_query(
                    index=index_name,
                    body=Search().query(qry).to_dict(),
                    refresh=True)
                return res["deleted"]
            except ConnectionTimeout:
                self.logger.exception("ES request timeout")
                time.sleep(3)
                self._connect()
                continue
            except Exception as e:
                self.logger.warning("ESConnection.delete got exception: " + str(e))
                if re.search(r"(not_found)", str(e), re.IGNORECASE):
                    return 0
        return 0