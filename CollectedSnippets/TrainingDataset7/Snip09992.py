def get_constraints(self, cursor, table_name):
        """
        Retrieve any constraints or keys (unique, pk, fk, check, index) across
        one or more columns.
        """
        constraints = {}
        # Find inline check constraints.
        try:
            table_schema = cursor.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' and name=%s",
                [table_name],
            ).fetchone()[0]
        except TypeError:
            # table_name is a view.
            pass
        else:
            columns = {
                info.name for info in self.get_table_description(cursor, table_name)
            }
            constraints.update(self._parse_table_constraints(table_schema, columns))

        # Get the index info
        cursor.execute(
            "PRAGMA index_list(%s)" % self.connection.ops.quote_name(table_name)
        )
        for row in cursor.fetchall():
            # Discard last 2 columns.
            number, index, unique = row[:3]
            cursor.execute(
                "SELECT sql FROM sqlite_master WHERE type='index' AND name=%s",
                [index],
            )
            # There's at most one row.
            (sql,) = cursor.fetchone() or (None,)
            # Inline constraints are already detected in
            # _parse_table_constraints(). The reasons to avoid fetching inline
            # constraints from `PRAGMA index_list` are:
            # - Inline constraints can have a different name and information
            #   than what `PRAGMA index_list` gives.
            # - Not all inline constraints may appear in `PRAGMA index_list`.
            if not sql:
                # An inline constraint
                continue
            # Get the index info for that index
            cursor.execute(
                "PRAGMA index_info(%s)" % self.connection.ops.quote_name(index)
            )
            for index_rank, column_rank, column in cursor.fetchall():
                if index not in constraints:
                    constraints[index] = {
                        "columns": [],
                        "primary_key": False,
                        "unique": bool(unique),
                        "foreign_key": None,
                        "check": False,
                        "index": True,
                    }
                constraints[index]["columns"].append(column)
            # Add type and column orders for indexes
            if constraints[index]["index"]:
                # SQLite doesn't support any index type other than b-tree
                constraints[index]["type"] = Index.suffix
                orders = self._get_index_columns_orders(sql)
                if orders is not None:
                    constraints[index]["orders"] = orders
        # Get the PK
        pk_columns = self.get_primary_key_columns(cursor, table_name)
        if pk_columns:
            # SQLite doesn't actually give a name to the PK constraint,
            # so we invent one. This is fine, as the SQLite backend never
            # deletes PK constraints by name, as you can't delete constraints
            # in SQLite; we remake the table with a new PK instead.
            constraints["__primary__"] = {
                "columns": pk_columns,
                "primary_key": True,
                "unique": False,  # It's not actually a unique constraint.
                "foreign_key": None,
                "check": False,
                "index": False,
            }
        relations = enumerate(self.get_relations(cursor, table_name).items())
        constraints.update(
            {
                f"fk_{index}": {
                    "columns": [column_name],
                    "primary_key": False,
                    "unique": False,
                    "foreign_key": (ref_table_name, ref_column_name),
                    "check": False,
                    "index": False,
                }
                for index, (
                    column_name,
                    (ref_column_name, ref_table_name, _),
                ) in relations
            }
        )
        return constraints