def _expression_refs_exclude(cls, model, expression, exclude):
        get_field = model._meta.get_field
        for field_name, *__ in model._get_expr_references(expression):
            if field_name == "pk":
                field = model._meta.pk
            else:
                field = get_field(field_name)
            if field_name in exclude or field.name in exclude:
                return True
            if field.generated and cls._expression_refs_exclude(
                model, field.expression, exclude
            ):
                return True
        return False