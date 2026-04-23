def sql_flush(self, style, tables, *, reset_sequences=False, allow_cascade=False):
        if not tables:
            return []

        truncated_tables = {table.upper() for table in tables}
        constraints = set()
        # Oracle's TRUNCATE CASCADE only works with ON DELETE CASCADE foreign
        # keys which Django doesn't define. Emulate the PostgreSQL behavior
        # which truncates all dependent tables by manually retrieving all
        # foreign key constraints and resolving dependencies.
        for table in tables:
            for foreign_table, constraint in self._foreign_key_constraints(
                table, recursive=allow_cascade
            ):
                if allow_cascade:
                    truncated_tables.add(foreign_table)
                constraints.add((foreign_table, constraint))
        sql = (
            [
                "%s %s %s %s %s %s %s %s;"
                % (
                    style.SQL_KEYWORD("ALTER"),
                    style.SQL_KEYWORD("TABLE"),
                    style.SQL_FIELD(self.quote_name(table)),
                    style.SQL_KEYWORD("DISABLE"),
                    style.SQL_KEYWORD("CONSTRAINT"),
                    style.SQL_FIELD(self.quote_name(constraint)),
                    style.SQL_KEYWORD("KEEP"),
                    style.SQL_KEYWORD("INDEX"),
                )
                for table, constraint in constraints
            ]
            + [
                "%s %s %s;"
                % (
                    style.SQL_KEYWORD("TRUNCATE"),
                    style.SQL_KEYWORD("TABLE"),
                    style.SQL_FIELD(self.quote_name(table)),
                )
                for table in truncated_tables
            ]
            + [
                "%s %s %s %s %s %s;"
                % (
                    style.SQL_KEYWORD("ALTER"),
                    style.SQL_KEYWORD("TABLE"),
                    style.SQL_FIELD(self.quote_name(table)),
                    style.SQL_KEYWORD("ENABLE"),
                    style.SQL_KEYWORD("CONSTRAINT"),
                    style.SQL_FIELD(self.quote_name(constraint)),
                )
                for table, constraint in constraints
            ]
        )
        if reset_sequences:
            sequences = [
                sequence
                for sequence in self.connection.introspection.sequence_list()
                if sequence["table"].upper() in truncated_tables
            ]
            # Since we've just deleted all the rows, running our sequence ALTER
            # code will reset the sequence to 0.
            sql.extend(self.sequence_reset_by_name_sql(style, sequences))
        return sql