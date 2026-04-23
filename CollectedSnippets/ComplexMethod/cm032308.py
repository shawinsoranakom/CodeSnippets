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
        memory_ids: list[str],
        agg_fields: list[str] | None = None,
        rank_feature: dict | None = None,
        hide_forgotten: bool = True
    ):
        """Search messages in memory storage."""
        if isinstance(index_names, str):
            index_names = index_names.split(",")
        assert isinstance(index_names, list) and len(index_names) > 0

        result: SearchResult = SearchResult(total=0, messages=[])

        output_fields = select_fields.copy()
        if "id" not in output_fields:
            output_fields = ["id"] + output_fields
        if "_score" in output_fields:
            output_fields.remove("_score")

        # Handle content_embed field - resolve to actual vector column name
        has_content_embed = "content_embed" in output_fields
        actual_vector_column: Optional[str] = None
        if has_content_embed:
            output_fields = [f for f in output_fields if f != "content_embed"]
            # Try to get vector column name from first available table
            for idx_name in index_names:
                if self._check_table_exists_cached(idx_name):
                    actual_vector_column = self._get_vector_column_name_from_table(idx_name)
                    if actual_vector_column:
                        output_fields.append(actual_vector_column)
                        break

        if highlight_fields:
            for field in highlight_fields:
                field_name = self.convert_field_name(field)
                if field_name not in output_fields:
                    output_fields.append(field_name)

        db_output_fields = [self.convert_field_name(f) for f in output_fields]
        fields_expr = ", ".join(db_output_fields)

        condition["memory_id"] = memory_ids
        if hide_forgotten:
            condition["must_not"] = {"exists": "forget_at"}

        condition_dict = {self.convert_field_name(k): v for k, v in condition.items()}
        filters: list[str] = self._get_filters(condition_dict)
        filters_expr = " AND ".join(filters) if filters else "1=1"

        # Parse match expressions
        fulltext_query: Optional[str] = None
        fulltext_topn: Optional[int] = None
        fulltext_search_expr: dict[str, str] = {}
        fulltext_search_weight: dict[str, float] = {}
        fulltext_search_filter: Optional[str] = None
        fulltext_search_score_expr: Optional[str] = None

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
            elif isinstance(m, MatchDenseExpr):
                vector_column_name = m.vector_column_name
                vector_data = m.embedding_data
                vector_topn = m.topn
                vector_similarity_threshold = m.extra_options.get("similarity", 0.0) if m.extra_options else 0.0
            elif isinstance(m, FusionExpr):
                weights = m.fusion_params.get("weights", "0.5,0.5") if m.fusion_params else "0.5,0.5"
                vector_similarity_weight = get_float(weights.split(",")[1])

        if fulltext_query:
            fulltext_search_filter = f"({' OR '.join([expr for expr in fulltext_search_expr.values()])})"
            fulltext_search_score_expr = f"({' + '.join(f'{expr} * {fulltext_search_weight.get(col, 0)}' for col, expr in fulltext_search_expr.items())})"

        if vector_data:
            vector_data_str = "[" + ",".join([str(np.float32(v)) for v in vector_data]) + "]"
            vector_search_expr = vector_search_template % (vector_column_name, vector_data_str)
            vector_search_score_expr = f"(1 - {vector_search_expr})"
            vector_search_filter = f"{vector_search_score_expr} >= {vector_similarity_threshold}"

        # Determine search type
        if fulltext_query and vector_data:
            search_type = "fusion"
        elif fulltext_query:
            search_type = "fulltext"
        elif vector_data:
            search_type = "vector"
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
            table_name = index_name

            if not self._check_table_exists_cached(table_name):
                continue

            if search_type == "fusion":
                num_candidates = (vector_topn or limit) + (fulltext_topn or limit)
                score_expr = f"(relevance * {1 - vector_similarity_weight} + {vector_search_score_expr} * {vector_similarity_weight})"
                fusion_sql = (
                    f"WITH fulltext_results AS ("
                    f"  SELECT *, {fulltext_search_score_expr} AS relevance"
                    f"      FROM {table_name}"
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
                self.logger.debug("OBConnection.search with fusion sql: %s", fusion_sql)
                rows, elapsed_time = self._execute_search_sql(fusion_sql)
                self.logger.info(
                    f"OBConnection.search table {table_name}, search type: fusion, elapsed time: {elapsed_time:.3f}s, rows: {len(rows)}"
                )

                for row in rows:
                    result.messages.append(self._row_to_entity(row, db_output_fields + ["_score"]))
                    result.total += 1

            elif search_type == "vector":
                vector_sql = self._build_vector_search_sql(
                    table_name, fields_expr, vector_search_score_expr, filters_expr,
                    vector_search_filter, vector_search_expr, limit, vector_topn, offset
                )
                self.logger.debug("OBConnection.search with vector sql: %s", vector_sql)
                rows, elapsed_time = self._execute_search_sql(vector_sql)
                self.logger.info(
                    f"OBConnection.search table {table_name}, search type: vector, elapsed time: {elapsed_time:.3f}s, rows: {len(rows)}"
                )

                for row in rows:
                    result.messages.append(self._row_to_entity(row, db_output_fields + ["_score"]))
                    result.total += 1

            elif search_type == "fulltext":
                fulltext_sql = self._build_fulltext_search_sql(
                    table_name, fields_expr, fulltext_search_score_expr, filters_expr,
                    fulltext_search_filter, offset, limit, fulltext_topn
                )
                self.logger.debug("OBConnection.search with fulltext sql: %s", fulltext_sql)
                rows, elapsed_time = self._execute_search_sql(fulltext_sql)
                self.logger.info(
                    f"OBConnection.search table {table_name}, search type: fulltext, elapsed time: {elapsed_time:.3f}s, rows: {len(rows)}"
                )

                for row in rows:
                    result.messages.append(self._row_to_entity(row, db_output_fields + ["_score"]))
                    result.total += 1

            else:
                orders: list[str] = []
                if order_by and order_by.fields:
                    for field, order_dir in order_by.fields:
                        field_name = self.convert_field_name(field)
                        order_str = "ASC" if order_dir == 0 else "DESC"
                        orders.append(f"{field_name} {order_str}")

                order_by_expr = ("ORDER BY " + ", ".join(orders)) if orders else ""
                limit_expr = f"LIMIT {offset}, {limit}" if limit != 0 else ""
                filter_sql = self._build_filter_search_sql(
                    table_name, fields_expr, filters_expr, order_by_expr, limit_expr
                )
                self.logger.debug("OBConnection.search with filter sql: %s", filter_sql)
                rows, elapsed_time = self._execute_search_sql(filter_sql)
                self.logger.info(
                    f"OBConnection.search table {table_name}, search type: filter, elapsed time: {elapsed_time:.3f}s, rows: {len(rows)}"
                )

                for row in rows:
                    result.messages.append(self._row_to_entity(row, db_output_fields))
                    result.total += 1

        if result.total == 0:
            result.total = len(result.messages)

        return result, result.total