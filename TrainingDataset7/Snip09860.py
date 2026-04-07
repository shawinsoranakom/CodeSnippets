def distinct_sql(self, fields, params):
        if fields:
            params = [param for param_list in params for param in param_list]
            return (["DISTINCT ON (%s)" % ", ".join(fields)], params)
        else:
            return ["DISTINCT"], []