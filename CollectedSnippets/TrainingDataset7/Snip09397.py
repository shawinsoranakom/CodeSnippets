def _index_condition_sql(self, condition):
        if condition:
            return " WHERE " + condition
        return ""