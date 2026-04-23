def get_placeholder_sql(self, value, compiler, connection):
        db_type = self.db_type(connection)
        if hasattr(value, "as_sql"):
            sql, params = compiler.compile(value)
            return f"{sql}::{db_type}", params
        return f"%s::{db_type}", (value,)