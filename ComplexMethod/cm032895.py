def update(self, condition: dict, new_value: dict, index_name: str, knowledgebase_id: str) -> bool:
        # if 'position_int' in newValue:
        #     logger.info(f"update position_int: {newValue['position_int']}")
        inf_conn = self.connPool.get_conn()
        try:
            db_instance = inf_conn.get_database(self.dbName)
            if index_name.startswith("ragflow_doc_meta_"):
                table_name = index_name
            else:
                table_name = f"{index_name}_{knowledgebase_id}"
            table_instance = db_instance.get_table(table_name)
            # if "exists" in condition:
            #    del condition["exists"]

            clmns = {}
            if table_instance:
                for n, ty, de, _ in table_instance.show_columns().rows():
                    clmns[n] = (ty, de)
            filter = self.equivalent_condition_to_str(condition, table_instance)
            removeValue = {}
            for k, v in list(new_value.items()):
                if k == "docnm_kwd":
                    new_value["docnm"] = self.list2str(v)
                elif k == "title_kwd":
                    if not new_value.get("docnm_kwd"):
                        new_value["docnm"] = self.list2str(v)
                elif k == "title_sm_tks":
                    if not new_value.get("docnm_kwd"):
                        new_value["docnm"] = v
                elif k == "important_kwd":
                    if isinstance(v, list):
                        empty_count = sum(1 for kw in v if kw == "")
                        tokens = [kw for kw in v if kw != ""]
                        new_value["important_keywords"] = self.list2str(tokens, ",")
                        new_value["important_kwd_empty_count"] = empty_count
                    else:
                        new_value["important_keywords"] = self.list2str(v, ",")
                elif k == "important_tks":
                    if not new_value.get("important_kwd"):
                        new_value["important_keywords"] = v
                elif k == "content_with_weight":
                    new_value["content"] = v
                elif k == "content_ltks":
                    if not new_value.get("content_with_weight"):
                        new_value["content"] = v
                elif k == "content_sm_ltks":
                    if not new_value.get("content_with_weight"):
                        new_value["content"] = v
                elif k == "authors_tks":
                    new_value["authors"] = v
                elif k == "authors_sm_tks":
                    if not new_value.get("authors_tks"):
                        new_value["authors"] = v
                elif k == "question_kwd":
                    new_value["questions"] = "\n".join(v)
                elif k == "question_tks":
                    if not new_value.get("question_kwd"):
                        new_value["questions"] = self.list2str(v)
                elif self.field_keyword(k):
                    if isinstance(v, list):
                        new_value[k] = "###".join(v)
                    else:
                        new_value[k] = v
                elif re.search(r"_feas$", k):
                    new_value[k] = json.dumps(v)
                elif k == "kb_id":
                    if isinstance(new_value[k], list):
                        new_value[k] = new_value[k][0]  # since d[k] is a list, but we need a str
                elif k == "position_int":
                    assert isinstance(v, list)
                    arr = [num for row in v for num in row]
                    new_value[k] = "_".join(f"{num:08x}" for num in arr)
                elif k in ["page_num_int", "top_int"]:
                    assert isinstance(v, list)
                    new_value[k] = "_".join(f"{num:08x}" for num in v)
                elif k == "remove":
                    if isinstance(v, str):
                        assert v in clmns, f"'{v}' should be in '{clmns}'."
                        ty, de = clmns[v]
                        if ty.lower().find("cha"):
                            if not de:
                                de = ""
                        new_value[v] = de
                    else:
                        for kk, vv in v.items():
                            removeValue[kk] = vv
                        del new_value[k]
                else:
                    new_value[k] = v
            for k in ["docnm_kwd", "title_tks", "title_sm_tks", "important_kwd", "important_tks", "content_with_weight",
                      "content_ltks", "content_sm_ltks", "authors_tks", "authors_sm_tks", "question_kwd", "question_tks"]:
                if k in new_value:
                    del new_value[k]

            remove_opt = {}  # "[k,new_value]": [id_to_update, ...]
            if removeValue:
                col_to_remove = list(removeValue.keys())
                row_to_opt = table_instance.output(col_to_remove + ["id"]).filter(filter).to_df()
                self.logger.debug(f"INFINITY search table {str(table_name)}, filter {filter}, result: {str(row_to_opt[0])}")
                row_to_opt = self.get_fields(row_to_opt, col_to_remove)
                for id, old_v in row_to_opt.items():
                    for k, remove_v in removeValue.items():
                        if remove_v in old_v[k]:
                            new_v = old_v[k].copy()
                            new_v.remove(remove_v)
                            kv_key = json.dumps([k, new_v])
                            if kv_key not in remove_opt:
                                remove_opt[kv_key] = [id]
                            else:
                                remove_opt[kv_key].append(id)

            self.logger.debug(f"INFINITY update table {table_name}, filter {filter}, newValue {new_value}.")
            for update_kv, ids in remove_opt.items():
                k, v = json.loads(update_kv)
                table_instance.update(filter + " AND id in ({0})".format(",".join([f"'{id}'" for id in ids])),
                                      {k: "###".join(v)})

            table_instance.update(filter, new_value)
        finally:
            self.connPool.release_conn(inf_conn)
        return True