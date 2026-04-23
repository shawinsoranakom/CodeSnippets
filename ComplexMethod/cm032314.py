def search(
            self, select_fields: list[str],
            highlight_fields: list[str],
            condition: dict,
            match_expressions: list[MatchExpr],
            order_by: OrderByExpr,
            offset: int,
            limit: int,
            index_names: str | list[str],
            memory_ids: list[str],
            agg_fields: list[str] | None = None,
            rank_feature: dict | None = None,
            hide_forgotten: bool = True
    ):
        """
        Refers to https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html
        """
        if isinstance(index_names, str):
            index_names = index_names.split(",")
        assert isinstance(index_names, list) and len(index_names) > 0
        assert "_id" not in condition

        exist_index_list = [idx for idx in index_names if self.index_exist(idx)]
        if not exist_index_list:
            return None, 0

        bool_query = Q("bool", must=[], must_not=[])
        if hide_forgotten:
            # filter not forget
            bool_query.must_not.append(Q("exists", field="forget_at"))

        condition["memory_id"] = memory_ids
        for k, v in condition.items():
            field_name = self.convert_field_name(k)
            if field_name == "session_id" and v:
                bool_query.filter.append(Q("query_string", **{"query": f"*{v}*", "fields": ["session_id"], "analyze_wildcard": True}))
                continue
            if not v:
                continue
            if isinstance(v, list):
                bool_query.filter.append(Q("terms", **{field_name: v}))
            elif isinstance(v, str) or isinstance(v, int):
                bool_query.filter.append(Q("term", **{field_name: v}))
            else:
                raise Exception(
                    f"Condition `{str(k)}={str(v)}` value type is {str(type(v))}, expected to be int, str or list.")
        s = Search()
        vector_similarity_weight = 0.5
        for m in match_expressions:
            if isinstance(m, FusionExpr) and m.method == "weighted_sum" and "weights" in m.fusion_params:
                assert len(match_expressions) == 3 and isinstance(match_expressions[0], MatchTextExpr) and isinstance(match_expressions[1],
                                                                                                                      MatchDenseExpr) and isinstance(
                    match_expressions[2], FusionExpr)
                weights = m.fusion_params["weights"]
                vector_similarity_weight = get_float(weights.split(",")[1])
        for m in match_expressions:
            if isinstance(m, MatchTextExpr):
                minimum_should_match = m.extra_options.get("minimum_should_match", 0.0)
                if isinstance(minimum_should_match, float):
                    minimum_should_match = str(int(minimum_should_match * 100)) + "%"
                bool_query.must.append(Q("query_string", fields=[self.convert_field_name(f, use_tokenized_content=True) for f in m.fields],
                                   type="best_fields", query=m.matching_text,
                                   minimum_should_match=minimum_should_match,
                                   boost=1))
                bool_query.boost = 1.0 - vector_similarity_weight

            elif isinstance(m, MatchDenseExpr):
                assert (bool_query is not None)
                similarity = 0.0
                if "similarity" in m.extra_options:
                    similarity = m.extra_options["similarity"]
                s = s.knn(self.convert_field_name(m.vector_column_name),
                          m.topn,
                          m.topn * 2,
                          query_vector=list(m.embedding_data),
                          filter=bool_query.to_dict(),
                          similarity=similarity,
                          )

        if bool_query and rank_feature:
            for fld, sc in rank_feature.items():
                if fld != PAGERANK_FLD:
                    fld = f"{TAG_FLD}.{fld}"
                bool_query.should.append(Q("rank_feature", field=fld, linear={}, boost=sc))

        if bool_query:
            s = s.query(bool_query)
        for field in highlight_fields:
            s = s.highlight(field)

        if order_by:
            orders = list()
            for field, order in order_by.fields:
                order = "asc" if order == 0 else "desc"
                if field.endswith("_int") or field.endswith("_flt"):
                    order_info = {"order": order, "unmapped_type": "float"}
                else:
                    order_info = {"order": order, "unmapped_type": "text"}
                orders.append({field: order_info})
            s = s.sort(*orders)

        if agg_fields:
            for fld in agg_fields:
                s.aggs.bucket(f'aggs_{fld}', 'terms', field=fld, size=1000000)

        if limit > 0:
            s = s[offset:offset + limit]
        q = s.to_dict()
        self.logger.debug(f"ESConnection.search {str(index_names)} query: " + json.dumps(q))

        for i in range(ATTEMPT_TIME):
            try:
                #print(json.dumps(q, ensure_ascii=False))
                res = self.es.search(index=exist_index_list,
                                     body=q,
                                     timeout="600s",
                                     # search_type="dfs_query_then_fetch",
                                     track_total_hits=True,
                                     _source=True)
                if str(res.get("timed_out", "")).lower() == "true":
                    raise Exception("Es Timeout.")
                self.logger.debug(f"ESConnection.search {str(index_names)} res: " + str(res))
                return res, self.get_total(res)
            except ConnectionTimeout:
                self.logger.exception("ES request timeout")
                self._connect()
                continue
            except NotFoundError as e:
                self.logger.debug(f"ESConnection.search {str(index_names)} query: " + str(q) + str(e))
                return None, 0
            except Exception as e:
                self.logger.exception(f"ESConnection.search {str(index_names)} query: " + str(q) + str(e))
                raise e

        self.logger.error(f"ESConnection.search timeout for {ATTEMPT_TIME} times!")
        raise Exception("ESConnection.search timeout.")