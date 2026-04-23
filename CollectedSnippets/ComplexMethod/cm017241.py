def get_constraints(self, cursor, table_name):
        """
        Retrieve any constraints or keys (unique, pk, fk, check, index) across
        one or more columns.
        """
        constraints = {}
        # Get the actual constraint names and columns
        name_query = """
            SELECT kc.`constraint_name`, kc.`column_name`,
                kc.`referenced_table_name`, kc.`referenced_column_name`,
                c.`constraint_type`
            FROM
                information_schema.key_column_usage AS kc,
                information_schema.table_constraints AS c
            WHERE
                kc.table_schema = DATABASE() AND
                (
                    kc.referenced_table_schema = DATABASE() OR
                    kc.referenced_table_schema IS NULL
                ) AND
                c.table_schema = kc.table_schema AND
                c.constraint_name = kc.constraint_name AND
                c.constraint_type != 'CHECK' AND
                kc.table_name = %s
            ORDER BY kc.`ordinal_position`
        """
        cursor.execute(name_query, [table_name])
        for constraint, column, ref_table, ref_column, kind in cursor.fetchall():
            if constraint not in constraints:
                constraints[constraint] = {
                    "columns": OrderedSet(),
                    "primary_key": kind == "PRIMARY KEY",
                    "unique": kind in {"PRIMARY KEY", "UNIQUE"},
                    "index": False,
                    "check": False,
                    "foreign_key": (ref_table, ref_column) if ref_column else None,
                }
                if self.connection.features.supports_index_column_ordering:
                    constraints[constraint]["orders"] = []
            constraints[constraint]["columns"].add(column)
        # Add check constraints.
        if self.connection.features.can_introspect_check_constraints:
            unnamed_constraints_index = 0
            columns = {
                info.name for info in self.get_table_description(cursor, table_name)
            }
            if self.connection.mysql_is_mariadb:
                type_query = """
                    SELECT c.constraint_name, c.check_clause
                    FROM information_schema.check_constraints AS c
                    WHERE
                        c.constraint_schema = DATABASE() AND
                        c.table_name = %s
                """
            else:
                type_query = """
                    SELECT cc.constraint_name, cc.check_clause
                    FROM
                        information_schema.check_constraints AS cc,
                        information_schema.table_constraints AS tc
                    WHERE
                        cc.constraint_schema = DATABASE() AND
                        tc.table_schema = cc.constraint_schema AND
                        cc.constraint_name = tc.constraint_name AND
                        tc.constraint_type = 'CHECK' AND
                        tc.table_name = %s
                """
            cursor.execute(type_query, [table_name])
            for constraint, check_clause in cursor.fetchall():
                constraint_columns = self._parse_constraint_columns(
                    check_clause, columns
                )
                # Ensure uniqueness of unnamed constraints. Unnamed unique
                # and check columns constraints have the same name as
                # a column.
                if set(constraint_columns) == {constraint}:
                    unnamed_constraints_index += 1
                    constraint = "__unnamed_constraint_%s__" % unnamed_constraints_index
                constraints[constraint] = {
                    "columns": constraint_columns,
                    "primary_key": False,
                    "unique": False,
                    "index": False,
                    "check": True,
                    "foreign_key": None,
                }
        # Now add in the indexes
        cursor.execute(
            "SHOW INDEX FROM %s" % self.connection.ops.quote_name(table_name)
        )
        for table, non_unique, index, colseq, column, order, type_ in [
            x[:6] + (x[10],) for x in cursor.fetchall()
        ]:
            if index not in constraints:
                constraints[index] = {
                    "columns": OrderedSet(),
                    "primary_key": False,
                    "unique": not non_unique,
                    "check": False,
                    "foreign_key": None,
                }
                if self.connection.features.supports_index_column_ordering:
                    constraints[index]["orders"] = []
            constraints[index]["index"] = True
            constraints[index]["type"] = (
                Index.suffix if type_ == "BTREE" else type_.lower()
            )
            constraints[index]["columns"].add(column)
            if self.connection.features.supports_index_column_ordering:
                constraints[index]["orders"].append("DESC" if order == "D" else "ASC")
        # Convert the sorted sets to lists
        for constraint in constraints.values():
            constraint["columns"] = list(constraint["columns"])
        return constraints