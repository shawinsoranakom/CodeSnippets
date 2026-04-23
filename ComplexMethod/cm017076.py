def _should_embed_body_fields(fields: list[ModelField]) -> bool:
    if not fields:
        return False
    # More than one dependency could have the same field, it would show up as multiple
    # fields but it's the same one, so count them by name
    body_param_names_set = {field.name for field in fields}
    # A top level field has to be a single field, not multiple
    if len(body_param_names_set) > 1:
        return True
    first_field = fields[0]
    # If it explicitly specifies it is embedded, it has to be embedded
    if getattr(first_field.field_info, "embed", None):
        return True
    # If it's a Form (or File) field, it has to be a BaseModel (or a union of BaseModels) to be top level
    # otherwise it has to be embedded, so that the key value pair can be extracted
    if (
        isinstance(first_field.field_info, params.Form)
        and not lenient_issubclass(first_field.field_info.annotation, BaseModel)
        and not is_union_of_base_models(first_field.field_info.annotation)
    ):
        return True
    return False