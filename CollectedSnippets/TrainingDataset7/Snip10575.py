def default_alias(self):
        expressions = [
            expr for expr in self.get_source_expressions() if expr is not None
        ]
        if len(expressions) == 1 and hasattr(expressions[0], "name"):
            return "%s__%s" % (expressions[0].name, self.name.lower())
        raise TypeError("Complex expressions require an alias")