def insert(self, documents: list[dict], index_name: str, knowledgebase_id: str = None) -> list[str]:
        '''
        # Save input to file to test inserting from file in GO
        import datetime
        import os
        debug_file = os.path.join("/var/infinity/tmp", f"insert_{index_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json")
        with open(debug_file, 'w') as f:
            json.dump({
                "table_name": index_name,
                "knowledgebase_id": knowledgebase_id,
                "chunks": documents
            }, f, indent=2)
        self.logger.debug(f"Saved insert input to {debug_file}")
        '''

        inf_conn = self.connPool.get_conn()
        try:
            db_instance = inf_conn.get_database(self.dbName)
            if index_name.startswith("ragflow_doc_meta_"):
                table_name = index_name
            else:
                table_name = f"{index_name}_{knowledgebase_id}"
            try:
                table_instance = db_instance.get_table(table_name)
            except InfinityException as e:
                # src/common/status.cppm, kTableNotExist = 3022
                if e.error_code != ErrorCode.TABLE_NOT_EXIST:
                    raise
                vector_size = 0
                patt = re.compile(r"q_(?P<vector_size>\d+)_vec")
                for k in documents[0].keys():
                    m = patt.match(k)
                    if m:
                        vector_size = int(m.group("vector_size"))
                        break
                if vector_size == 0:
                    raise ValueError("Cannot infer vector size from documents")

                # Determine parser_id from document structure
                # Table parser documents have 'chunk_data' field
                parser_id = None
                if "chunk_data" in documents[0] and isinstance(documents[0].get("chunk_data"), dict):
                    from common.constants import ParserType
                    parser_id = ParserType.TABLE.value
                    self.logger.debug("Detected TABLE parser from document structure")

                # Fallback: Create table with base schema (shouldn't normally happen as init_kb() creates it)
                self.logger.debug(f"Fallback: Creating table {table_name} with base schema, parser_id: {parser_id}")
                self.create_idx(index_name, knowledgebase_id, vector_size, parser_id)
                table_instance = db_instance.get_table(table_name)

            # embedding fields can't have a default value....
            embedding_clmns = []
            clmns = table_instance.show_columns().rows()
            for n, ty, _, _ in clmns:
                r = re.search(r"Embedding\([a-z]+,([0-9]+)\)", ty)
                if not r:
                    continue
                embedding_clmns.append((n, int(r.group(1))))

            docs = copy.deepcopy(documents)
            for d in docs:
                assert "_id" not in d
                assert "id" in d
                for k, v in list(d.items()):
                    if k == "docnm_kwd":
                        d["docnm"] = v
                    elif k == "title_kwd":
                        if not d.get("docnm_kwd"):
                            d["docnm"] = self.list2str(v)
                    elif k == "title_sm_tks":
                        if not d.get("docnm_kwd"):
                            d["docnm"] = self.list2str(v)
                    elif k == "important_kwd":
                        if isinstance(v, list):
                            empty_count = sum(1 for kw in v if kw == "")
                            tokens = [kw for kw in v if kw != ""]
                            d["important_keywords"] = self.list2str(tokens, ",")
                            d["important_kwd_empty_count"] = empty_count
                        else:
                            d["important_keywords"] = self.list2str(v, ",")
                    elif k == "important_tks":
                        if not d.get("important_kwd"):
                            d["important_keywords"] = v
                    elif k == "content_with_weight":
                        d["content"] = v
                    elif k == "content_ltks":
                        if not d.get("content_with_weight"):
                            d["content"] = v
                    elif k == "content_sm_ltks":
                        if not d.get("content_with_weight"):
                            d["content"] = v
                    elif k == "authors_tks":
                        d["authors"] = v
                    elif k == "authors_sm_tks":
                        if not d.get("authors_tks"):
                            d["authors"] = v
                    elif k == "question_kwd":
                        d["questions"] = self.list2str(v, "\n")
                    elif k == "question_tks":
                        if not d.get("question_kwd"):
                            d["questions"] = self.list2str(v)
                    elif self.field_keyword(k):
                        if isinstance(v, list):
                            d[k] = "###".join(v)
                        else:
                            d[k] = v
                    elif re.search(r"_feas$", k):
                        d[k] = json.dumps(v)
                    elif k == "chunk_data":
                        # Convert data dict to JSON string for storage
                        if isinstance(v, dict):
                            d[k] = json.dumps(v)
                        else:
                            d[k] = v
                    elif k == "kb_id":
                        if isinstance(d[k], list):
                            d[k] = d[k][0]  # since d[k] is a list, but we need a str
                    elif k == "position_int":
                        assert isinstance(v, list)
                        arr = [num for row in v for num in row]
                        d[k] = "_".join(f"{num:08x}" for num in arr)
                    elif k in ["page_num_int", "top_int"]:
                        assert isinstance(v, list)
                        d[k] = "_".join(f"{num:08x}" for num in v)
                    elif k == "meta_fields":
                        if isinstance(v, dict):
                            d[k] = json.dumps(v, ensure_ascii=False)
                        else:
                            d[k] = v if v else "{}"
                    else:
                        d[k] = v
                for k in ["docnm_kwd", "title_tks", "title_sm_tks", "important_kwd", "important_tks", "content_with_weight",
                          "content_ltks", "content_sm_ltks", "authors_tks", "authors_sm_tks", "question_kwd",
                          "question_tks"]:
                    if k in d:
                        del d[k]

                for n, vs in embedding_clmns:
                    if n in d:
                        continue
                    d[n] = [0] * vs
            ids = ["'{}'".format(d["id"]) for d in docs]
            str_ids = ", ".join(ids)
            str_filter = f"id IN ({str_ids})"
            table_instance.delete(str_filter)
            # for doc in documents:
            #     logger.info(f"insert position_int: {doc['position_int']}")
            # logger.info(f"InfinityConnection.insert {json.dumps(documents)}")
            table_instance.insert(docs)
        finally:
            self.connPool.release_conn(inf_conn)
        self.logger.debug(f"INFINITY inserted into {table_name} {str_ids}.")
        return []