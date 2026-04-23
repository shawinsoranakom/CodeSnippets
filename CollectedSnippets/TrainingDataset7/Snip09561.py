def sql_flush(self, style, tables, *, reset_sequences=False, allow_cascade=False):
        if not tables:
            return []

        sql = ["SET FOREIGN_KEY_CHECKS = 0;"]
        if reset_sequences:
            # It's faster to TRUNCATE tables that require a sequence reset
            # since ALTER TABLE AUTO_INCREMENT is slower than TRUNCATE.
            sql.extend(
                "%s %s;"
                % (
                    style.SQL_KEYWORD("TRUNCATE"),
                    style.SQL_FIELD(self.quote_name(table_name)),
                )
                for table_name in tables
            )
        else:
            # Otherwise issue a simple DELETE since it's faster than TRUNCATE
            # and preserves sequences.
            sql.extend(
                "%s %s %s;"
                % (
                    style.SQL_KEYWORD("DELETE"),
                    style.SQL_KEYWORD("FROM"),
                    style.SQL_FIELD(self.quote_name(table_name)),
                )
                for table_name in tables
            )
        sql.append("SET FOREIGN_KEY_CHECKS = 1;")
        return sql