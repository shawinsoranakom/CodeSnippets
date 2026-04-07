def fk_on_delete_sql(self, operation):
        """
        Return the SQL to make an ON DELETE statement.
        """
        if operation in ["CASCADE", "SET NULL", "SET DEFAULT"]:
            return f" ON DELETE {operation}"
        if operation == "":
            return ""
        raise NotImplementedError(f"ON DELETE {operation} is not supported.")