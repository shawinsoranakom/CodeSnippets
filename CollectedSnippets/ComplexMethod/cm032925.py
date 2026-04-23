def search(
            self, select_fields: list[str],
            highlight_fields: list[str],
            condition: dict,
            match_expressions: list[MatchExpr],
            order_by: OrderByExpr,
            offset: int,
            limit: int,
            index_names: str | list[str],
            knowledgebase_ids: list[str],
            agg_fields: list[str] | None = None,
            rank_feature: dict | None = None
    ):
        """
        Refers to https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html
        """
        if isinstance(index_names, str):
            index_names = index_names.split(",")
        assert isinstance(index_names, list) and len(index_names) > 0
        assert "_id" not in condition

        bool_query = Q("bool", must=[])
        condition["kb_id"] = knowledgebase_ids
        for k, v in condition.items():
            if k == "available_int":
                if v == 0:
                    bool_query.filter.append(Q("range", available_int={"lt": 1}))
                else:
                    bool_query.filter.append(
                        Q("bool", must_not=Q("range", available_int={"lt": 1})))
                continue
            if not v:
                continue
            if isinstance(v, list):
                bool_query.filter.append(Q("terms", **{k: v}))
            elif isinstance(v, str) or isinstance(v, int):
                bool_query.filter.append(Q("term", **{k: v}))
            else:
                raise Exception(
                    f"Condition `{str(k)}={str(v)}` value type is {str(type(v))}, expected to be int, str or list.")

        s = Search()
        vector_similarity_weight = 0.5
        for m in match_expressions:
            if isinstance(m, FusionExpr) and m.method == "weighted_sum" and "weights" in m.fusion_params:
                assert len(match_expressions) == 3 and isinstance(match_expressions[0], MatchTextExpr) and isinstance(
                    match_expressions[1],
                    MatchDenseExpr) and isinstance(
                    match_expressions[2], FusionExpr)
                weights = m.fusion_params["weights"]
                vector_similarity_weight = get_float(weights.split(",")[1])
        for m in match_expressions:
            if isinstance(m, MatchTextExpr):
                minimum_should_match = m.extra_options.get("minimum_should_match", 0.0)
                if isinstance(minimum_should_match, float):
                    minimum_should_match = str(int(minimum_should_match * 100)) + "%"
                bool_query.must.append(Q("query_string", fields=m.fields,
                                         type="best_fields", query=m.matching_text,
                                         minimum_should_match=minimum_should_match,
                                         boost=1))
                bool_query.boost = 1.0 - vector_similarity_weight

            elif isinstance(m, MatchDenseExpr):
                assert (bool_query is not None)
                similarity = 0.0
                if "similarity" in m.extra_options:
                    similarity = m.extra_options["similarity"]
                s = s.knn(m.vector_column_name,
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
                if field in ["page_num_int", "top_int"]:
                    order_info = {"order": order, "unmapped_type": "float",
                                  "mode": "avg", "numeric_type": "double"}
                elif field.endswith("_int") or field.endswith("_flt"):
                    order_info = {"order": order, "unmapped_type": "float"}
                else:
                    order_info = {"order": order, "unmapped_type": "text"}
                orders.append({field: order_info})
            s = s.sort(*orders)
        if agg_fields:
            for fld in agg_fields:
                s.aggs.bucket(f'aggs_{fld}', 'terms', field=fld, size=1000000)

        has_dense = any(isinstance(m, MatchDenseExpr) for m in match_expressions)
        has_explicit_sort = bool(order_by and order_by.fields)
        use_search_after = (
            limit > 0
            and (offset + limit > MAX_RESULT_WINDOW)
            and has_explicit_sort
            and not has_dense
        )

        if limit > 0 and not use_search_after:
            s = s[offset:offset + limit]
        # Filter _source to only requested fields for efficiency, and add vector
        # fields to "fields" param so they appear in hit.fields when ES 9.x
        # exclude_source_vectors is enabled (dense_vector not in _source).
        if select_fields:
            s = s.source(select_fields)
        q = s.to_dict()
        # ES 9.x: dense_vector fields excluded from _source; request them via fields.
        # Note: knn does NOT have a "fields" parameter - adding it inside the knn
        # object causes BadRequestError on ES 9.x. We add "fields" at top level.
        vector_fields = [f for f in (select_fields or []) if f.endswith("_vec")]
        if vector_fields:
            q["fields"] = vector_fields
        self.logger.debug(f"ESConnection.search {str(index_names)} query: " + json.dumps(q))

        for i in range(ATTEMPT_TIME):
            try:
                if use_search_after:
                    res = self._search_with_search_after(index_names, q, offset, limit)
                else:
                    # print(json.dumps(q, ensure_ascii=False))
                    res = self._es_search_once(index_names, q, track_total_hits=True)
                if str(res.get("timed_out", "")).lower() == "true":
                    raise Exception("Es Timeout.")
                self.logger.debug(f"ESConnection.search {str(index_names)} res: " + str(res))
                return res
            except ConnectionTimeout:
                self.logger.exception("ES request timeout")
                self._connect()
                continue
            except Exception as e:
                # Only log debug for NotFoundError(accepted when metadata index doesn't exist)
                if 'NotFound' in str(e):
                    self.logger.debug(f"ESConnection.search {str(index_names)} query: " + str(q) + " - " + str(e))
                else:
                    self.logger.exception(f"ESConnection.search {str(index_names)} query: " + str(q) + str(e))
                raise e

        self.logger.error(f"ESConnection.search timeout for {ATTEMPT_TIME} times!")
        raise Exception("ESConnection.search timeout.")