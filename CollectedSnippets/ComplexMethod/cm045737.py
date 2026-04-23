def create_table(self, schema: type[pw.Schema], *, add_special_fields: bool) -> str:
        table_name = self.random_table_name()

        primary_key_found = False
        fields = []
        for field_name, field_schema in schema.columns().items():
            parts = [f"`{field_name}`"]
            field_type = field_schema.dtype
            if field_type == dtype.STR:
                parts.append("VARCHAR(255)")
            elif field_type == dtype.INT:
                parts.append("BIGINT")
            elif field_type == dtype.FLOAT:
                parts.append("DOUBLE")
            elif field_type == dtype.BOOL:
                parts.append("BOOLEAN")
            else:
                raise RuntimeError(f"Unsupported field type {field_type}")
            if field_schema.primary_key:
                if primary_key_found:
                    raise AssertionError("Only single primary key supported")
                primary_key_found = True
                parts.append("PRIMARY KEY NOT NULL")
            fields.append(" ".join(parts))

        if add_special_fields:
            fields.append("`time` BIGINT NOT NULL")
            fields.append("`diff` BIGINT NOT NULL")

        create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({','.join(fields)})"
        self.cursor.execute(create_sql)
        return table_name