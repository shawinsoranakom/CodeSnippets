def get_placeholder_sql(self, value, compiler, connection):
                placeholder = get_placeholder(self, value, compiler, connection)
                if hasattr(value, "as_sql"):
                    sql, params = compiler.compile(value)
                    return placeholder % sql, params
                return placeholder, (value,)