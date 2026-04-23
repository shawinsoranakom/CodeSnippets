def _migrate_db(self, inf_conn):
        inf_db = inf_conn.create_database(self.dbName, ConflictType.Ignore)
        fp_mapping = os.path.join(get_project_base_directory(), "conf", self.mapping_file_name)
        if not os.path.exists(fp_mapping):
            raise Exception(f"Mapping file not found at {fp_mapping}")
        with open(fp_mapping) as f:
            schema = json.load(f)
        table_names = inf_db.list_tables().table_names
        for table_name in table_names:
            if not table_name.startswith(self.table_name_prefix):
                # Skip tables not created by me
                continue
            inf_table = inf_db.get_table(table_name)
            index_names = inf_table.list_indexes().index_names
            if "q_vec_idx" not in index_names:
                # Skip tables not created by me
                continue
            column_names = inf_table.show_columns()["name"]
            column_names = set(column_names)
            for field_name, field_info in schema.items():
                is_new_column = field_name not in column_names
                if is_new_column:
                    res = inf_table.add_columns({field_name: field_info})
                    assert res.error_code == infinity.ErrorCode.OK
                    self.logger.info(f"INFINITY added following column to table {table_name}: {field_name} {field_info}")

                if field_info["type"] == "varchar" and "analyzer" in field_info:
                    analyzers = field_info["analyzer"]
                    if isinstance(analyzers, str):
                        analyzers = [analyzers]
                    for analyzer in analyzers:
                        inf_table.create_index(
                            f"ft_{re.sub(r'[^a-zA-Z0-9]', '_', field_name)}_{re.sub(r'[^a-zA-Z0-9]', '_', analyzer)}",
                            IndexInfo(field_name, IndexType.FullText, {"ANALYZER": analyzer}),
                            ConflictType.Ignore,
                        )

                if "index_type" in field_info:
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