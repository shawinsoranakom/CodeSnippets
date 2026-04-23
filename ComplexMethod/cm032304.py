def insert(self, documents: list[dict], index_name: str, memory_id: str = None) -> list[str]:
        if not documents:
            return []
        inf_conn = self.connPool.get_conn()
        try:
            db_instance = inf_conn.get_database(self.dbName)
            table_name = f"{index_name}_{memory_id}"
            vector_size = int(len(documents[0]["content_embed"]))
            try:
                table_instance = db_instance.get_table(table_name)
            except InfinityException as e:
                # src/common/status.cppm, kTableNotExist = 3022
                if e.error_code != ErrorCode.TABLE_NOT_EXIST:
                    raise
                if vector_size == 0:
                    raise ValueError("Cannot infer vector size from documents")
                self.create_idx(index_name, memory_id, vector_size)
                table_instance = db_instance.get_table(table_name)

            # embedding fields can't have a default value....
            embedding_columns = []
            table_columns = table_instance.show_columns().rows()
            for n, ty, _, _ in table_columns:
                r = re.search(r"Embedding\([a-z]+,([0-9]+)\)", ty)
                if not r:
                    continue
                embedding_columns.append((n, int(r.group(1))))

            docs = copy.deepcopy(documents)
            for d in docs:
                assert "_id" not in d
                assert "id" in d
                for k, v in list(d.items()):
                    if k == "content_embed":
                        d[f"q_{vector_size}_vec"] = d["content_embed"]
                        d.pop("content_embed")
                        continue
                    field_name = self.convert_message_field_to_infinity(k)
                    if field_name in ["valid_at", "invalid_at", "forget_at"]:
                        d[f"{field_name}_flt"] = date_string_to_timestamp(v) if v else 0
                        if v is None:
                            d[field_name] = ""
                    elif self.field_keyword(k):
                        if isinstance(v, list):
                            d[k] = "###".join(v)
                        else:
                            d[k] = v
                    elif k == "memory_id":
                        if isinstance(d[k], list):
                            d[k] = d[k][0]  # since d[k] is a list, but we need a str
                    else:
                        d[field_name] = v
                    if k != field_name:
                        d.pop(k)

                for n, vs in embedding_columns:
                    if n in d:
                        continue
                    d[n] = [0] * vs
            ids = ["'{}'".format(d["id"]) for d in docs]
            str_ids = ", ".join(ids)
            str_filter = f"id IN ({str_ids})"
            table_instance.delete(str_filter)
            table_instance.insert(docs)
        finally:
            self.connPool.release_conn(inf_conn)
        self.logger.debug(f"INFINITY inserted into {table_name} {str_ids}.")
        return []