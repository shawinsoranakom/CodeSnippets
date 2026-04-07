def as_sql(
        self, compiler, connection, template=None, case_joiner=None, **extra_context
    ):
        connection.ops.check_expression_support(self)
        if not self.cases:
            return compiler.compile(self.default)
        template_params = {**self.extra, **extra_context}
        case_parts = []
        sql_params = []
        for case in self.cases:
            try:
                case_sql, case_params = compiler.compile(case)
            except EmptyResultSet:
                continue
            except FullResultSet:
                default = case.result
                break
            case_parts.append(case_sql)
            sql_params.extend(case_params)
        else:
            default = self.default
        if case_parts:
            default_sql, default_params = compiler.compile(default)
        else:
            if (
                isinstance(default, Value)
                and (output_field := default._output_field_or_none) is not None
            ):
                from django.db.models.functions import Cast

                default = Cast(default, output_field)
            return compiler.compile(default)

        case_joiner = case_joiner or self.case_joiner
        template_params["cases"] = case_joiner.join(case_parts)
        template_params["default"] = default_sql
        sql_params.extend(default_params)
        template = template or template_params.get("template", self.template)
        sql = template % template_params
        if self._output_field_or_none is not None:
            sql = connection.ops.unification_cast_sql(self.output_field) % sql
        return sql, tuple(sql_params)