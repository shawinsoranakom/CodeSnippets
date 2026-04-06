def get_validation_alias(field: ModelField) -> str:
    va = getattr(field, "validation_alias", None)
    return va or field.alias