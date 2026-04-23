def process_rhs(self, compiler, connection):
        if isinstance(self.rhs, KeyTransform):
            return super(lookups.Exact, self).process_rhs(compiler, connection)
        rhs, rhs_params = super().process_rhs(compiler, connection)
        if connection.vendor == "oracle":
            func = []
            sql = "%s(JSON_OBJECT('value' VALUE %%s FORMAT JSON), '$.value')"
            for value in rhs_params:
                value = json.loads(value)
                if isinstance(value, (list, dict)):
                    func.append(sql % "JSON_QUERY")
                else:
                    func.append(sql % "JSON_VALUE")
            rhs %= tuple(func)
        elif connection.vendor == "sqlite":
            func = []
            for value in rhs_params:
                if value in connection.ops.jsonfield_datatype_values:
                    func.append("%s")
                else:
                    func.append("JSON_EXTRACT(%s, '$')")
            rhs %= tuple(func)
        return rhs, rhs_params