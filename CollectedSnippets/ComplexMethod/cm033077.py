def create_idx(self, index_name: str, dataset_id: str, vector_size: int, parser_id: str = None):
        table_name = f"{index_name}_{dataset_id}"
        self.logger.debug(f"CREATE_IDX: Creating table {table_name}, parser_id: {parser_id}")

        inf_conn = self.connPool.get_conn()
        try:
            inf_db = inf_conn.create_database(self.dbName, ConflictType.Ignore)

            # Use configured schema
            fp_mapping = os.path.join(get_project_base_directory(), "conf", self.mapping_file_name)
            if not os.path.exists(fp_mapping):
                raise Exception(f"Mapping file not found at {fp_mapping}")
            with open(fp_mapping) as f:
                schema = json.load(f)

            if parser_id is not None:
                from common.constants import ParserType

                if parser_id == ParserType.TABLE.value:
                    # Table parser: add chunk_data JSON column to store table-specific fields
                    schema["chunk_data"] = {"type": "json", "default": "{}"}
                    self.logger.info("Added chunk_data column for TABLE parser")

            vector_name = f"q_{vector_size}_vec"
            schema[vector_name] = {"type": f"vector,{vector_size},float"}
            inf_table = inf_db.create_table(
                table_name,
                schema,
                ConflictType.Ignore,
            )
            inf_table.create_index(
                "q_vec_idx",
                IndexInfo(
                    vector_name,
                    IndexType.Hnsw,
                    {
                        "M": "16",
                        "ef_construction": "50",
                        "metric": "cosine",
                        "encode": "lvq",
                    },
                ),
                ConflictType.Ignore,
            )
            for field_name, field_info in schema.items():
                if field_info["type"] != "varchar" or "analyzer" not in field_info:
                    continue
                analyzers = field_info["analyzer"]
                if isinstance(analyzers, str):
                    analyzers = [analyzers]
                for analyzer in analyzers:
                    inf_table.create_index(
                        f"ft_{re.sub(r'[^a-zA-Z0-9]', '_', field_name)}_{re.sub(r'[^a-zA-Z0-9]', '_', analyzer)}",
                        IndexInfo(field_name, IndexType.FullText, {"ANALYZER": analyzer}),
                        ConflictType.Ignore,
                    )

            # Create secondary indexes for fields with index_type
            for field_name, field_info in schema.items():
                if "index_type" not in field_info:
                    continue
                index_config = field_info["index_type"]
                if isinstance(index_config, str) and index_config == "secondary":
                    inf_table.create_index(
                        f"sec_{field_name}",
                        IndexInfo(field_name, IndexType.Secondary),
                        ConflictType.Ignore,
                    )
                    self.logger.info(f"INFINITY created secondary index sec_{field_name} for field {field_name}")
                elif isinstance(index_config, dict):
                    if index_config.get("type") == "secondary":
                        params = {}
                        if "cardinality" in index_config:
                            params = {"cardinality": index_config["cardinality"]}
                        inf_table.create_index(
                            f"sec_{field_name}",
                            IndexInfo(field_name, IndexType.Secondary, params),
                            ConflictType.Ignore,
                        )
                        self.logger.info(f"INFINITY created secondary index sec_{field_name} for field {field_name} with params {params}")

            self.logger.info(f"INFINITY created table {table_name}, vector size {vector_size}")
            return True
        finally:
            self.connPool.release_conn(inf_conn)