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
            agg_fields: list[str] | None = None,
            rank_feature: dict | None = None,
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
            output = select_fields.copy()
            output = self.convert_select_fields(output)
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
                if score_func and score_func not in output:
                    output.append(score_func)
                if PAGERANK_FLD not in output:
                    output.append(PAGERANK_FLD)
            output = [f for f in output if f and f != "_score"]
            if limit <= 0:
                # ElasticSearch default limit is 10000
                limit = 10000

            # Prepare expressions common to all tables
            filter_cond = None
            filter_fulltext = ""
            if condition:
                # For metadata table (ragflow_doc_meta_), keep kb_id filter
                # For chunk tables, remove kb_id filter as they use table separation per KB
                is_meta_table = any(indexName.startswith("ragflow_doc_meta_") for indexName in index_names)
                if not is_meta_table:
                    condition = {k: v for k, v in condition.items() if k != "kb_id"}

                table_found = False
                for indexName in index_names:
                    if indexName.startswith("ragflow_doc_meta_"):
                        table_names_to_search = [indexName]
                    else:
                        table_names_to_search = [f"{indexName}_{kb_id}" for kb_id in knowledgebase_ids]
                    for table_name in table_names_to_search:
                        try:
                            filter_cond = self.equivalent_condition_to_str(condition, db_instance.get_table(table_name))
                            table_found = True
                            break
                        except Exception:
                            pass
                    if table_found:
                        break
                if not table_found:
                    self.logger.error(
                        f"No valid tables found for indexNames {index_names} and knowledgebaseIds {knowledgebase_ids}")
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

                    # Add rank_feature support
                    if rank_feature and "rank_features" not in matchExpr.extra_options:
                        # Convert rank_feature dict to Infinity's rank_features string format
                        # Format: "field^feature_name^weight,field^feature_name^weight"
                        rank_features_list = []
                        for feature_name, weight in rank_feature.items():
                            # Use TAG_FLD as the field containing rank features
                            rank_features_list.append(f"{TAG_FLD}^{feature_name}^{weight}")
                        if rank_features_list:
                            matchExpr.extra_options["rank_features"] = ",".join(rank_features_list)

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
                    if order_field[1] == 0:
                        order_by_expr_list.append((order_field[0], SortType.Asc))
                    else:
                        order_by_expr_list.append((order_field[0], SortType.Desc))

            total_hits_count = 0
            # Scatter search tables and gather the results
            for indexName in index_names:
                if indexName.startswith("ragflow_doc_meta_"):
                    table_names_to_search = [indexName]
                else:
                    table_names_to_search = [f"{indexName}_{kb_id}" for kb_id in knowledgebase_ids]
                for table_name in table_names_to_search:
                    try:
                        table_instance = db_instance.get_table(table_name)
                    except Exception:
                        continue
                    table_list.append(table_name)
                    builder = table_instance.output(output)
                    if len(match_expressions) > 0:
                        for matchExpr in match_expressions:
                            if isinstance(matchExpr, MatchTextExpr):
                                fields = ",".join(matchExpr.fields)
                                self.logger.info(f"INFINITY search match_text: {matchExpr.matching_text}")
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
                    kb_res, extra_result = builder.option({"total_hits_count": True}).to_df()
                    if extra_result:
                        total_hits_count += int(extra_result["total_hits_count"])
                    self.logger.debug(f"INFINITY search table: {str(table_name)}, result: {str(kb_res)}")
                    df_list.append(kb_res)
            res = self.concat_dataframes(df_list, output)
            if match_expressions and score_column:
                res["_score"] = res[score_column] + res[PAGERANK_FLD]
                res = res.sort_values(by="_score", ascending=False).reset_index(drop=True)
                res = res.head(limit)
            self.logger.debug(f"INFINITY search final result: {str(res)}")
            return res, total_hits_count
        finally:
            self.connPool.release_conn(inf_conn)