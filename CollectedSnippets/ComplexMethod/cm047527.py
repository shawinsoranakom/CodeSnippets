def _check_inherits(model_cls: type[BaseModel]):
    for comodel_name, field_name in model_cls._inherits.items():
        field = model_cls._fields.get(field_name)
        if not field or field.type != 'many2one':
            raise TypeError(
                f"Missing many2one field definition for _inherits reference {field_name!r} in model {model_cls._name!r}. "
                f"Add a field like: {field_name} = fields.Many2one({comodel_name!r}, required=True, ondelete='cascade')"
            )
        if not (field.delegate and field.required and (field.ondelete or "").lower() in ("cascade", "restrict")):
            raise TypeError(
                f"Field definition for _inherits reference {field_name!r} in {model_cls._name!r} "
                "must be marked as 'delegate', 'required' with ondelete='cascade' or 'restrict'"
            )