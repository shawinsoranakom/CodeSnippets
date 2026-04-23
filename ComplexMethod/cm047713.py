def populate_field(model: Model, field: Field, populated: dict[Model, int], factors: dict[Model, int],
                   table_alias: str = 't', series_alias: str = 's') -> SQL | None:
    """
    Returns the source expression for copying the field (SQL(identifier|expression|subquery) | None)
    `table_alias` and `series_alias` are the identifiers used to reference
    the currently being populated table and it's series, respectively.
    """
    def copy_noop():
        return None

    def copy_raw(field_):
        return SQL.identifier(field_.name)

    def copy(field_):
        if field_needs_variation(model, field_):
            return get_field_variation(model, field_, factors[model], series_alias)
        else:
            return copy_raw(field_)

    def copy_id():
        last_id = fetch_last_id(model)
        populated[model] = last_id  # this adds the model in the populated dict
        return SQL('id + %(last_id)s * %(series_alias)s', last_id=last_id, series_alias=SQL.identifier(series_alias))

    def copy_many2one(field_):
        # if the comodel was priorly populated, remap the many2one to the new copies
        if (comodel := model.env[field_.comodel_name]) in populated:
            comodel_max_id = populated[comodel]
            # we use MOD() instead of %, because % cannot be correctly escaped, it's a limitation of the SQL wrapper
            return SQL("%(table_alias)s.%(field_name)s + %(comodel_max_id)s * (MOD(%(series_alias)s - 1, %(factor)s) + 1)",
                        table_alias=SQL.identifier(table_alias),
                        field_name=SQL.identifier(field_.name),
                        comodel_max_id=comodel_max_id,
                        series_alias=SQL.identifier(series_alias),
                        factor=factors[comodel])
        return copy(field_)

    if field.name == 'id':
        return copy_id()
    match field.type:
        case 'one2many':
            # there is nothing to copy, as it's value is implicitly read from the inverse Many2one
            return copy_noop()
        case 'many2many':
            # there is nothing to do, the copying of the m2m will be handled when copying the relation table
            return copy_noop()
        case 'many2one':
            return copy_many2one(field)
        case 'many2one_reference':
            # TODO: in the case of a reference field, there is no comodel,
            #  but it's specified as the value of the field specified by model_field.
            #  Not really sure how to handle this, as it involves reading the content pointed by model_field
            #  to check on-the-fly if it's populated or not python-side, so for now we raw-copy it.
            #  If we need to read on-the-fly, the populated structure needs to be in DB (via a new Model?)
            return copy(field)
        case 'binary':
            # copy only binary field that are inlined in the table
            return copy(field) if not field.attachment else copy_noop()
        case _:
            return copy(field)