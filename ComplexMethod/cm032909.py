def search(
        self,
        select_fields: list[str],
        highlight_fields: list[str],
        condition: dict,
        match_expressions: list[MatchExpr],
        order_by: OrderByExpr,
        offset: int,
        limit: int,
        index_names: str | list[str],
        knowledgebase_ids: list[str],
        agg_fields: list[str] = [],
        rank_feature: dict | None = None,
        **kwargs,
    ):
        if isinstance(index_names, str):
            index_names = index_names.split(",")
        assert isinstance(index_names, list) and len(index_names) > 0
        index_names = list(set(index_names))

        if len(match_expressions) == 3:
            if not self.enable_fulltext_search:
                # disable fulltext search in fusion search, which means fallback to vector search
                match_expressions = [m for m in match_expressions if isinstance(m, MatchDenseExpr)]
            else:
                for m in match_expressions:
                    if isinstance(m, FusionExpr):
                        weights = m.fusion_params["weights"]
                        vector_similarity_weight = get_float(weights.split(",")[1])
                        # skip the search if its weight is zero
                        if vector_similarity_weight <= 0.0:
                            match_expressions = [m for m in match_expressions if isinstance(m, MatchTextExpr)]
                        elif vector_similarity_weight >= 1.0:
                            match_expressions = [m for m in match_expressions if isinstance(m, MatchDenseExpr)]

        result: SearchResult = SearchResult(
            total=0,
            chunks=[],
        )

        # copied from es_conn.py
        if len(match_expressions) == 3 and self.es:
            bqry = Q("bool", must=[])
            condition["kb_id"] = knowledgebase_ids
            for k, v in condition.items():
                if k == "available_int":
                    if v == 0:
                        bqry.filter.append(Q("range", available_int={"lt": 1}))
                    else:
                        bqry.filter.append(
                            Q("bool", must_not=Q("range", available_int={"lt": 1})))
                    continue
                if not v:
                    continue
                if isinstance(v, list):
                    bqry.filter.append(Q("terms", **{k: v}))
                elif isinstance(v, str) or isinstance(v, int):
                    bqry.filter.append(Q("term", **{k: v}))
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
                    bqry.must.append(Q("query_string", fields=FTS_COLUMNS_TKS,
                                       type="best_fields", query=m.matching_text,
                                       minimum_should_match=minimum_should_match,
                                       boost=1))
                    bqry.boost = 1.0 - vector_similarity_weight

                elif isinstance(m, MatchDenseExpr):
                    assert (bqry is not None)
                    similarity = 0.0
                    if "similarity" in m.extra_options:
                        similarity = m.extra_options["similarity"]
                    s = s.knn(m.vector_column_name,
                              m.topn,
                              m.topn * 2,
                              query_vector=list(m.embedding_data),
                              filter=bqry.to_dict(),
                              similarity=similarity,
                              )

            if bqry and rank_feature:
                for fld, sc in rank_feature.items():
                    if fld != PAGERANK_FLD:
                        fld = f"{TAG_FLD}.{fld}"
                    bqry.should.append(Q("rank_feature", field=fld, linear={}, boost=sc))

            if bqry:
                s = s.query(bqry)
            # for field in highlightFields:
            #     s = s.highlight(field)

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

            for fld in agg_fields:
                s.aggs.bucket(f'aggs_{fld}', 'terms', field=fld, size=1000000)

            if limit > 0:
                s = s[offset:offset + limit]
            q = s.to_dict()
            logger.debug(f"OBConnection.hybrid_search {str(index_names)} query: " + json.dumps(q))

            for index_name in index_names:
                start_time = time.time()
                res = self.es.search(index=index_name,
                                     body=q,
                                     timeout="600s",
                                     track_total_hits=True,
                                     _source=True)
                elapsed_time = time.time() - start_time
                logger.info(
                    f"OBConnection.search table {index_name}, search type: hybrid, elapsed time: {elapsed_time:.3f} seconds,"
                    f" got count: {len(res)}"
                )
                for chunk in res:
                    result.chunks.append(self._es_row_to_entity(chunk))
                    result.total = result.total + 1
            return result

        output_fields = select_fields.copy()
        if "*" in output_fields:
            if index_names[0].startswith("ragflow_doc_meta_"):
                output_fields = doc_meta_column_names.copy()
            else:
                output_fields = column_names.copy()

        if "id" not in output_fields:
            output_fields = ["id"] + output_fields
        if "_score" in output_fields:
            output_fields.remove("_score")

        if highlight_fields:
            for field in highlight_fields:
                if field not in output_fields:
                    output_fields.append(field)

        fields_expr = ", ".join(output_fields)

        condition["kb_id"] = knowledgebase_ids
        filters: list[str] = get_filters(condition)
        filters_expr = " AND ".join(filters)

        fulltext_query: Optional[str] = None
        fulltext_topn: Optional[int] = None
        fulltext_search_weight: dict[str, float] = {}
        fulltext_search_expr: dict[str, str] = {}
        fulltext_search_idx_list: list[str] = []
        fulltext_search_score_expr: Optional[str] = None
        fulltext_search_filter: Optional[str] = None

        vector_column_name: Optional[str] = None
        vector_data: Optional[list[float]] = None
        vector_topn: Optional[int] = None
        vector_similarity_threshold: Optional[float] = None
        vector_similarity_weight: Optional[float] = None
        vector_search_expr: Optional[str] = None
        vector_search_score_expr: Optional[str] = None
        vector_search_filter: Optional[str] = None

        for m in match_expressions:
            if isinstance(m, MatchTextExpr):
                assert "original_query" in m.extra_options, "'original_query' is missing in extra_options."
                fulltext_query = m.extra_options["original_query"]
                fulltext_query = escape_string(fulltext_query.strip())
                fulltext_topn = m.topn

                fulltext_search_expr, fulltext_search_weight = self._parse_fulltext_columns(
                    fulltext_query, self._fulltext_search_columns
                )
                for column_name in fulltext_search_expr.keys():
                    fulltext_search_idx_list.append(fulltext_index_name_template % column_name)

            elif isinstance(m, MatchDenseExpr):
                assert m.embedding_data_type == "float", f"embedding data type '{m.embedding_data_type}' is not float."
                vector_column_name = m.vector_column_name
                vector_data = m.embedding_data
                vector_topn = m.topn
                vector_similarity_threshold = m.extra_options.get("similarity", 0.0)
            elif isinstance(m, FusionExpr):
                weights = m.fusion_params["weights"]
                vector_similarity_weight = get_float(weights.split(",")[1])

        if fulltext_query:
            fulltext_search_filter = f"({' OR '.join([expr for expr in fulltext_search_expr.values()])})"
            fulltext_search_score_expr = f"({' + '.join(f'{expr} * {fulltext_search_weight.get(col, 0)}' for col, expr in fulltext_search_expr.items())})"

        if vector_data:
            vector_data_str = "[" + ",".join([str(np.float32(v)) for v in vector_data]) + "]"
            vector_search_expr = vector_search_template % (vector_column_name, vector_data_str)
            # use (1 - cosine_distance) as score, which should be [-1, 1]
            # https://www.oceanbase.com/docs/common-oceanbase-database-standalone-1000000003577323
            vector_search_score_expr = f"(1 - {vector_search_expr})"
            vector_search_filter = f"{vector_search_score_expr} >= {vector_similarity_threshold}"

        pagerank_score_expr = f"(CAST(IFNULL({PAGERANK_FLD}, 0) AS DECIMAL(10, 2)) / 100)"

        # TODO use tag rank_feature in sorting
        # tag_rank_fea = {k: float(v) for k, v in (rank_feature or {}).items() if k != PAGERANK_FLD}

        if fulltext_query and vector_data:
            search_type = "fusion"
        elif fulltext_query:
            search_type = "fulltext"
        elif vector_data:
            search_type = "vector"
        elif len(agg_fields) > 0:
            search_type = "aggregation"
        else:
            search_type = "filter"

        if search_type in ["fusion", "fulltext", "vector"] and "_score" not in output_fields:
            output_fields.append("_score")

        if limit:
            if vector_topn is not None:
                limit = min(vector_topn, limit)
            if fulltext_topn is not None:
                limit = min(fulltext_topn, limit)

        for index_name in index_names:

            if not self._check_table_exists_cached(index_name):
                continue

            fulltext_search_hint = f"/*+ UNION_MERGE({index_name} {' '.join(fulltext_search_idx_list)}) */" if self.use_fulltext_hint else ""

            if search_type == "fusion":
                # fusion search, usually for chat
                num_candidates = vector_topn + fulltext_topn
                if self.use_fulltext_first_fusion_search:
                    count_sql = (
                        f"WITH fulltext_results AS ("
                        f"  SELECT {fulltext_search_hint} *, {fulltext_search_score_expr} AS relevance"
                        f"      FROM {index_name}"
                        f"      WHERE {filters_expr} AND {fulltext_search_filter}"
                        f"      ORDER BY relevance DESC"
                        f"      LIMIT {num_candidates}"
                        f")"
                        f"  SELECT COUNT(*) FROM fulltext_results WHERE {vector_search_filter}"
                    )
                else:
                    count_sql = (
                        f"WITH fulltext_results AS ("
                        f"  SELECT {fulltext_search_hint} id FROM {index_name}"
                        f"      WHERE {filters_expr} AND {fulltext_search_filter}"
                        f"      ORDER BY {fulltext_search_score_expr}"
                        f"      LIMIT {fulltext_topn}"
                        f"),"
                        f"vector_results AS ("
                        f"  SELECT id FROM {index_name}"
                        f"      WHERE {filters_expr} AND {vector_search_filter}"
                        f"      ORDER BY {vector_search_expr}"
                        f"      APPROXIMATE LIMIT {vector_topn}"
                        f")"
                        f"  SELECT COUNT(*) FROM fulltext_results f FULL OUTER JOIN vector_results v ON f.id = v.id"
                    )
                logger.debug("OBConnection.search with count sql: %s", count_sql)
                rows, elapsed_time = self._execute_search_sql(count_sql)
                total_count = rows[0][0] if rows else 0
                result.total += total_count
                logger.info(
                    f"OBConnection.search table {index_name}, search type: fusion, step: 1-count, elapsed time: {elapsed_time:.3f} seconds,"
                    f" vector column: '{vector_column_name}',"
                    f" query text: '{fulltext_query}',"
                    f" condition: '{condition}',"
                    f" vector_similarity_threshold: {vector_similarity_threshold},"
                    f" got count: {total_count}"
                )

                if total_count == 0:
                    continue

                if self.use_fulltext_first_fusion_search:
                    score_expr = f"(relevance * {1 - vector_similarity_weight} + {vector_search_score_expr} * {vector_similarity_weight} + {pagerank_score_expr})"
                    fusion_sql = (
                        f"WITH fulltext_results AS ("
                        f"  SELECT {fulltext_search_hint} *, {fulltext_search_score_expr} AS relevance"
                        f"      FROM {index_name}"
                        f"      WHERE {filters_expr} AND {fulltext_search_filter}"
                        f"      ORDER BY relevance DESC"
                        f"      LIMIT {num_candidates}"
                        f")"
                        f"  SELECT {fields_expr}, {score_expr} AS _score"
                        f"      FROM fulltext_results"
                        f"      WHERE {vector_search_filter}"
                        f"      ORDER BY _score DESC"
                        f"      LIMIT {offset}, {limit}"
                    )
                else:
                    pagerank_score_expr = f"(CAST(IFNULL(f.{PAGERANK_FLD}, 0) AS DECIMAL(10, 2)) / 100)"
                    score_expr = f"(f.relevance * {1 - vector_similarity_weight} + v.similarity * {vector_similarity_weight} + {pagerank_score_expr})"
                    fields_expr = ", ".join([f"t.{f} as {f}" for f in output_fields if f != "_score"])
                    fusion_sql = (
                        f"WITH fulltext_results AS ("
                        f"  SELECT {fulltext_search_hint} id, pagerank_fea, {fulltext_search_score_expr} AS relevance"
                        f"      FROM {index_name}"
                        f"      WHERE {filters_expr} AND {fulltext_search_filter}"
                        f"      ORDER BY relevance DESC"
                        f"      LIMIT {fulltext_topn}"
                        f"),"
                        f"vector_results AS ("
                        f"  SELECT id, pagerank_fea, {vector_search_score_expr} AS similarity"
                        f"      FROM {index_name}"
                        f"      WHERE {filters_expr} AND {vector_search_filter}"
                        f"      ORDER BY {vector_search_expr}"
                        f"      APPROXIMATE LIMIT {vector_topn}"
                        f"),"
                        f"combined_results AS ("
                        f"  SELECT COALESCE(f.id, v.id) AS id, {score_expr} AS score"
                        f"      FROM fulltext_results f"
                        f"      FULL OUTER JOIN vector_results v"
                        f"      ON f.id = v.id"
                        f")"
                        f"  SELECT {fields_expr}, c.score as _score"
                        f"      FROM combined_results c"
                        f"      JOIN {index_name} t"
                        f"      ON c.id = t.id"
                        f"      ORDER BY score DESC"
                        f"      LIMIT {offset}, {limit}"
                    )
                logger.debug("OBConnection.search with fusion sql: %s", fusion_sql)
                rows, elapsed_time = self._execute_search_sql(fusion_sql)
                logger.info(
                    f"OBConnection.search table {index_name}, search type: fusion, step: 2-query, elapsed time: {elapsed_time:.3f} seconds,"
                    f" select fields: '{output_fields}',"
                    f" vector column: '{vector_column_name}',"
                    f" query text: '{fulltext_query}',"
                    f" condition: '{condition}',"
                    f" vector_similarity_threshold: {vector_similarity_threshold},"
                    f" vector_similarity_weight: {vector_similarity_weight},"
                    f" return rows count: {len(rows)}"
                )

                for row in rows:
                    result.chunks.append(self._row_to_entity(row, output_fields))
            elif search_type == "vector":
                # vector search, usually used for graph search
                count_sql = self._build_count_sql(index_name, filters_expr, vector_search_filter)
                logger.debug("OBConnection.search with vector count sql: %s", count_sql)
                rows, elapsed_time = self._execute_search_sql(count_sql)
                total_count = rows[0][0] if rows else 0
                result.total += total_count
                logger.info(
                    f"OBConnection.search table {index_name}, search type: vector, step: 1-count, elapsed time: {elapsed_time:.3f} seconds,"
                    f" vector column: '{vector_column_name}',"
                    f" condition: '{condition}',"
                    f" vector_similarity_threshold: {vector_similarity_threshold},"
                    f" got count: {total_count}"
                )

                if total_count == 0:
                    continue

                vector_sql = self._build_vector_search_sql(
                    index_name, fields_expr, vector_search_score_expr, filters_expr,
                    vector_search_filter, vector_search_expr, limit, vector_topn, offset
                )
                logger.debug("OBConnection.search with vector sql: %s", vector_sql)
                rows, elapsed_time = self._execute_search_sql(vector_sql)
                logger.info(
                    f"OBConnection.search table {index_name}, search type: vector, step: 2-query, elapsed time: {elapsed_time:.3f} seconds,"
                    f" select fields: '{output_fields}',"
                    f" vector column: '{vector_column_name}',"
                    f" condition: '{condition}',"
                    f" vector_similarity_threshold: {vector_similarity_threshold},"
                    f" return rows count: {len(rows)}"
                )

                for row in rows:
                    result.chunks.append(self._row_to_entity(row, output_fields))
            elif search_type == "fulltext":
                # fulltext search, usually used to search chunks in one dataset
                count_sql = self._build_count_sql(index_name, filters_expr, fulltext_search_filter, fulltext_search_hint)
                logger.debug("OBConnection.search with fulltext count sql: %s", count_sql)
                rows, elapsed_time = self._execute_search_sql(count_sql)
                total_count = rows[0][0] if rows else 0
                result.total += total_count
                logger.info(
                    f"OBConnection.search table {index_name}, search type: fulltext, step: 1-count, elapsed time: {elapsed_time:.3f} seconds,"
                    f" query text: '{fulltext_query}',"
                    f" condition: '{condition}',"
                    f" got count: {total_count}"
                )

                if total_count == 0:
                    continue

                fulltext_sql = self._build_fulltext_search_sql(
                    index_name, fields_expr, fulltext_search_score_expr, filters_expr,
                    fulltext_search_filter, offset, limit, fulltext_topn, fulltext_search_hint
                )
                logger.debug("OBConnection.search with fulltext sql: %s", fulltext_sql)
                rows, elapsed_time = self._execute_search_sql(fulltext_sql)
                logger.info(
                    f"OBConnection.search table {index_name}, search type: fulltext, step: 2-query, elapsed time: {elapsed_time:.3f} seconds,"
                    f" select fields: '{output_fields}',"
                    f" query text: '{fulltext_query}',"
                    f" condition: '{condition}',"
                    f" return rows count: {len(rows)}"
                )

                for row in rows:
                    result.chunks.append(self._row_to_entity(row, output_fields))
            elif search_type == "aggregation":
                # aggregation search
                assert len(agg_fields) == 1, "Only one aggregation field is supported in OceanBase."
                agg_field = agg_fields[0]
                if agg_field in array_columns:
                    res = self.client.perform_raw_text_sql(
                        f"SELECT {agg_field} FROM {index_name}"
                        f" WHERE {agg_field} IS NOT NULL AND {filters_expr}"
                    )
                    counts = {}
                    for row in res:
                        if row[0]:
                            if isinstance(row[0], str):
                                try:
                                    arr = json.loads(row[0])
                                except json.JSONDecodeError:
                                    logger.warning(f"Failed to parse JSON array: {row[0]}")
                                    continue
                            else:
                                arr = row[0]

                            if isinstance(arr, list):
                                for v in arr:
                                    if isinstance(v, str) and v.strip():
                                        counts[v] = counts.get(v, 0) + 1

                    for v, count in counts.items():
                        result.chunks.append({
                            "value": v,
                            "count": count,
                        })
                    result.total += len(counts)
                else:
                    res = self.client.perform_raw_text_sql(
                        f"SELECT {agg_field}, COUNT(*) as count FROM {index_name}"
                        f" WHERE {agg_field} IS NOT NULL AND {filters_expr}"
                        f" GROUP BY {agg_field}"
                    )
                    for row in res:
                        result.chunks.append({
                            "value": row[0],
                            "count": int(row[1]),
                        })
                        result.total += 1
            else:
                # only filter
                orders: list[str] = []
                if order_by:
                    for field, order in order_by.fields:
                        if isinstance(column_types[field], ARRAY):
                            f = field + "_sort"
                            fields_expr += f", array_avg({field}) AS {f}"
                            field = f
                        order = "ASC" if order == 0 else "DESC"
                        orders.append(f"{field} {order}")
                count_sql = self._build_count_sql(index_name, filters_expr)
                logger.debug("OBConnection.search with normal count sql: %s", count_sql)
                rows, elapsed_time = self._execute_search_sql(count_sql)
                total_count = rows[0][0] if rows else 0
                result.total += total_count
                logger.info(
                    f"OBConnection.search table {index_name}, search type: normal, step: 1-count, elapsed time: {elapsed_time:.3f} seconds,"
                    f" condition: '{condition}',"
                    f" got count: {total_count}"
                )

                if total_count == 0:
                    continue

                order_by_expr = ("ORDER BY " + ", ".join(orders)) if len(orders) > 0 else ""
                limit_expr = f"LIMIT {offset}, {limit}" if limit != 0 else ""
                filter_sql = self._build_filter_search_sql(
                    index_name, fields_expr, filters_expr, order_by_expr, limit_expr
                )
                logger.debug("OBConnection.search with normal sql: %s", filter_sql)
                rows, elapsed_time = self._execute_search_sql(filter_sql)
                logger.info(
                    f"OBConnection.search table {index_name}, search type: normal, step: 2-query, elapsed time: {elapsed_time:.3f} seconds,"
                    f" select fields: '{output_fields}',"
                    f" condition: '{condition}',"
                    f" return rows count: {len(rows)}"
                )

                for row in rows:
                    result.chunks.append(self._row_to_entity(row, output_fields))

        if result.total == 0:
            result.total = len(result.chunks)

        return result