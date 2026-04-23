def create_table(self, schema: type[pw.Schema], *, add_special_fields: bool) -> str:
        table_name = self.random_table_name()

        primary_key_found = False
        fields = []
        for field_name, field_schema in schema.columns().items():
            parts = [field_name]
            field_type = field_schema.dtype
            if field_type == dtype.STR:
                parts.append("TEXT")
            elif field_type == dtype.INT:
                parts.append("BIGINT")
            elif field_type == dtype.FLOAT:
                parts.append("DOUBLE PRECISION")
            elif field_type == dtype.BOOL:
                parts.append("BOOLEAN")
            elif isinstance(field_type, dtype.Array) and "_vector" in field_name:
                # hack to create an array with a specific type
                parts.append("VECTOR")
            elif isinstance(field_type, dtype.Array) and "_halfvec" in field_name:
                # hack to create an array with a specific type
                parts.append("HALFVEC")
            else:
                raise RuntimeError(f"This test doesn't support field type {field_type}")
            if field_schema.primary_key:
                assert (
                    not primary_key_found
                ), "This test only supports simple primary keys"
                primary_key_found = True
                parts.append("PRIMARY KEY NOT NULL")
            fields.append(" ".join(parts))

        if add_special_fields:
            fields.append("time BIGINT NOT NULL")
            fields.append("diff BIGINT NOT NULL")

        self.cursor.execute(
            f'CREATE TABLE IF NOT EXISTS {table_name} ({",".join(fields)})'
        )

        return table_name