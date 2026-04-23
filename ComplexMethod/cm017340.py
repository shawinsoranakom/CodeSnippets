def _get_field_expression_map(self, meta, exclude=None):
        if exclude is None:
            exclude = set()
        meta = meta or self._meta
        field_map = {}
        generated_fields = []
        for field in meta.local_fields:
            if field.name in exclude:
                continue
            if field.generated:
                if any(
                    ref[0] in exclude
                    for ref in self._get_expr_references(field.expression)
                ):
                    continue
                generated_fields.append(field)
                continue
            if (
                isinstance(field.remote_field, ForeignObjectRel)
                and field not in meta.local_concrete_fields
            ):
                value = tuple(
                    getattr(self, from_field) for from_field in field.from_fields
                )
                if len(value) == 1:
                    value = value[0]
            elif field.concrete:
                value = getattr(self, field.attname)
            else:
                continue
            if not value or not hasattr(value, "resolve_expression"):
                value = Value(value, field)
            field_map[field.name] = value
            field_map[field.attname] = value
        if "pk" not in exclude:
            field_map["pk"] = Value(self.pk, meta.pk)
        if generated_fields:
            replacements = {F(name): value for name, value in field_map.items()}
            for generated_field in generated_fields:
                field_map[generated_field.name] = ExpressionWrapper(
                    generated_field.expression.replace_expressions(replacements),
                    generated_field.output_field,
                )

        return field_map