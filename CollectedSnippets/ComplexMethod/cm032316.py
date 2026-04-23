def get_missing_field_message(self, select_fields: list[str], index_name: str, memory_id: str, field_name: str, limit: int=512):
        if not self.index_exist(index_name):
            return None
        bool_query = Q("bool", must=[])
        bool_query.must.append(Q("term", memory_id=memory_id))
        bool_query.must_not.append(Q("exists", field=field_name))
        # from old to new
        order_by = OrderByExpr()
        order_by.asc("valid_at")
        # build search
        s = Search()
        s = s.query(bool_query)
        orders = list()
        for field, order in order_by.fields:
            order = "asc" if order == 0 else "desc"
            if field.endswith("_int") or field.endswith("_flt"):
                order_info = {"order": order, "unmapped_type": "float"}
            else:
                order_info = {"order": order, "unmapped_type": "text"}
            orders.append({field: order_info})
        s = s.sort(*orders)
        s = s[:limit]
        q = s.to_dict()
        # search
        for i in range(ATTEMPT_TIME):
            try:
                res = self.es.search(index=index_name, body=q, timeout="600s", track_total_hits=True, _source=True)
                if str(res.get("timed_out", "")).lower() == "true":
                    raise Exception("Es Timeout.")
                self.logger.debug(f"ESConnection.search {str(index_name)} res: " + str(res))
                return res
            except ConnectionTimeout:
                self.logger.exception("ES request timeout")
                self._connect()
                continue
            except NotFoundError as e:
                self.logger.debug(f"ESConnection.search {str(index_name)} query: " + str(q) + str(e))
                return None
            except Exception as e:
                self.logger.exception(f"ESConnection.search {str(index_name)} query: " + str(q) + str(e))
                raise e

        self.logger.error(f"ESConnection.search timeout for {ATTEMPT_TIME} times!")
        raise Exception("ESConnection.search timeout.")