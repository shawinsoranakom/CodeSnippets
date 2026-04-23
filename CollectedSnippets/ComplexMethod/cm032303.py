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
        hide_forgotten: bool = True,
    ) -> tuple[pd.DataFrame, int]:
        """
        BUG: Infinity returns empty for a highlight field if the query string doesn't use that field.
        """
        if isinstance(index_names, str):
            index_names = index_names.split(",")
        assert isinstance(index_names, list) and len(index_names) > 0
        inf_conn = self.connPool.get_conn()
        try:
            db_instance = inf_conn.get_database(self.dbName)
            df_list = list()
            table_list = list()
            if hide_forgotten:
                condition.update({"must_not": {"exists": "forget_at_flt"}})
            output = select_fields.copy()
            if agg_fields is None:
                agg_fields = []
            for essential_field in ["id"] + agg_fields:
                if essential_field not in output:
                    output.append(essential_field)
            score_func = ""
            score_column = ""
            for matchExpr in match_expressions:
                if isinstance(matchExpr, MatchTextExpr):
                    score_func = "score()"
                    score_column = "SCORE"
                    break
            if not score_func:
                for matchExpr in match_expressions:
                    if isinstance(matchExpr, MatchDenseExpr):
                        score_func = "similarity()"
                        score_column = "SIMILARITY"
                        break
            if match_expressions:
                if score_func not in output:
                    output.append(score_func)
            output = [f for f in output if f != "_score"]
            if limit <= 0:
                # ElasticSearch default limit is 10000
                limit = 10000

            # Prepare expressions common to all tables
            filter_cond = None
            filter_fulltext = ""
            if condition:
                condition_dict = {self.convert_condition_and_order_field(k): v for k, v in condition.items()}
                table_found = False
                for indexName in index_names:
                    for mem_id in memory_ids:
                        table_name = f"{indexName}_{mem_id}"
                        try:
                            filter_cond = self.equivalent_condition_to_str(condition_dict, db_instance.get_table(table_name))
                            table_found = True
                            break
                        except Exception:
                            pass
                    if table_found:
                        break
                if not table_found:
                    self.logger.error(f"No valid tables found for indexNames {index_names} and memoryIds {memory_ids}")
                    return pd.DataFrame(), 0

            for matchExpr in match_expressions:
                if isinstance(matchExpr, MatchTextExpr):
                    if filter_cond and "filter" not in matchExpr.extra_options:
                        matchExpr.extra_options.update({"filter": filter_cond})
                    matchExpr.fields = [self.convert_matching_field(field) for field in matchExpr.fields]
                    fields = ",".join(matchExpr.fields)
                    filter_fulltext = f"filter_fulltext('{fields}', '{matchExpr.matching_text}')"
                    if filter_cond:
                        filter_fulltext = f"({filter_cond}) AND {filter_fulltext}"
                    minimum_should_match = matchExpr.extra_options.get("minimum_should_match", 0.0)
                    if isinstance(minimum_should_match, float):
                        str_minimum_should_match = str(int(minimum_should_match * 100)) + "%"
                        matchExpr.extra_options["minimum_should_match"] = str_minimum_should_match

                    for k, v in matchExpr.extra_options.items():
                        if not isinstance(v, str):
                            matchExpr.extra_options[k] = str(v)
                    self.logger.debug(f"INFINITY search MatchTextExpr: {json.dumps(matchExpr.__dict__)}")
                elif isinstance(matchExpr, MatchDenseExpr):
                    if filter_fulltext and "filter" not in matchExpr.extra_options:
                        matchExpr.extra_options.update({"filter": filter_fulltext})
                    for k, v in matchExpr.extra_options.items():
                        if not isinstance(v, str):
                            matchExpr.extra_options[k] = str(v)
                    similarity = matchExpr.extra_options.get("similarity")
                    if similarity:
                        matchExpr.extra_options["threshold"] = similarity
                        del matchExpr.extra_options["similarity"]
                    self.logger.debug(f"INFINITY search MatchDenseExpr: {json.dumps(matchExpr.__dict__)}")
                elif isinstance(matchExpr, FusionExpr):
                    if matchExpr.method == "weighted_sum":
                        # The default is "minmax" which gives a zero score for the last doc.
                        matchExpr.fusion_params["normalize"] = "atan"
                    self.logger.debug(f"INFINITY search FusionExpr: {json.dumps(matchExpr.__dict__)}")

            order_by_expr_list = list()
            if order_by.fields:
                for order_field in order_by.fields:
                    order_field_name = self.convert_condition_and_order_field(order_field[0])
                    if order_field[1] == 0:
                        order_by_expr_list.append((order_field_name, SortType.Asc))
                    else:
                        order_by_expr_list.append((order_field_name, SortType.Desc))

            total_hits_count = 0
            # Scatter search tables and gather the results
            column_name_list = []
            for indexName in index_names:
                for memory_id in memory_ids:
                    table_name = f"{indexName}_{memory_id}"
                    try:
                        table_instance = db_instance.get_table(table_name)
                    except Exception:
                        continue
                    table_list.append(table_name)
                    if not column_name_list:
                        column_name_list = [r[0] for r in table_instance.show_columns().rows()]
                    output = self.convert_select_fields(output, column_name_list)
                    builder = table_instance.output(output)
                    if len(match_expressions) > 0:
                        for matchExpr in match_expressions:
                            if isinstance(matchExpr, MatchTextExpr):
                                fields = ",".join(matchExpr.fields)
                                builder = builder.match_text(
                                    fields,
                                    matchExpr.matching_text,
                                    matchExpr.topn,
                                    matchExpr.extra_options.copy(),
                                )
                            elif isinstance(matchExpr, MatchDenseExpr):
                                builder = builder.match_dense(
                                    matchExpr.vector_column_name,
                                    matchExpr.embedding_data,
                                    matchExpr.embedding_data_type,
                                    matchExpr.distance_type,
                                    matchExpr.topn,
                                    matchExpr.extra_options.copy(),
                                )
                            elif isinstance(matchExpr, FusionExpr):
                                builder = builder.fusion(matchExpr.method, matchExpr.topn, matchExpr.fusion_params)
                    else:
                        if filter_cond and len(filter_cond) > 0:
                            builder.filter(filter_cond)
                    if order_by.fields:
                        builder.sort(order_by_expr_list)
                    builder.offset(offset).limit(limit)
                    mem_res, extra_result = builder.option({"total_hits_count": True}).to_df()
                    if extra_result:
                        total_hits_count += int(extra_result["total_hits_count"])
                    self.logger.debug(f"INFINITY search table: {str(table_name)}, result: {str(mem_res)}")
                    df_list.append(mem_res)
        finally:
            self.connPool.release_conn(inf_conn)
        res = self.concat_dataframes(df_list, output)
        if match_expressions:
            res["_score"] = res[score_column]
            res = res.sort_values(by="_score", ascending=False).reset_index(drop=True)
            res = res.head(limit)
        self.logger.debug(f"INFINITY search final result: {str(res)}")
        return res, total_hits_count