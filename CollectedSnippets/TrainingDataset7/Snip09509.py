def as_sql(self):
        update_query, update_params = super().as_sql()
        # MySQL and MariaDB support UPDATE ... ORDER BY syntax.
        if self.query.order_by:
            order_by_sql = []
            order_by_params = []
            db_table = self.query.get_meta().db_table
            try:
                for resolved, (sql, params, _) in self.get_order_by():
                    if (
                        isinstance(resolved.expression, Col)
                        and resolved.expression.alias != db_table
                    ):
                        # Ignore ordering if it contains joined fields, because
                        # they cannot be used in the ORDER BY clause.
                        raise FieldError
                    order_by_sql.append(sql)
                    order_by_params.extend(params)
                update_query += " ORDER BY " + ", ".join(order_by_sql)
                update_params += tuple(order_by_params)
            except FieldError:
                # Ignore ordering if it contains annotations, because they're
                # removed in .update() and cannot be resolved.
                pass
        return update_query, update_params