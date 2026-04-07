def last_executed_query(self, cursor, sql, params):
            if self.connection.features.uses_server_side_binding:
                try:
                    return self.compose_sql(sql, params)
                except errors.DataError:
                    return super().last_executed_query(cursor, sql, params)
            else:
                if cursor._query and cursor._query.query is not None:
                    return cursor._query.query.decode()
                return super().last_executed_query(cursor, sql, params)