def populate_model(model: Model, populated: dict[Model, int], factors: dict[Model, int], separator_code: str) -> None:

    def update_sequence(model_):
        model_.env.execute_query(SQL("SELECT SETVAL(%(sequence)s, %(last_id)s, TRUE)",
                              sequence=f"{model_._table}_id_seq", last_id=fetch_last_id(model_)))

    def has_column(field_):
        return field_.store and field_.column_type

    assert model not in populated, f"We do not populate a model ({model}) that has already been populated."
    _logger.info('Populating model %s %s times...', model._name, factors[model])
    dest_fields = []
    src_fields = []
    update_fields = []
    table_alias = 't'
    series_alias = 's'
    # process all stored fields (that has a respective column), if the model has an 'id', it's processed first
    for _, field in sorted(model._fields.items(), key=lambda pair: pair[0] != 'id'):
        if has_column(field):
            if field_needs_variation(model, field) and field.type in ('char', 'text'):
                update_fields.append(field)
            if src := populate_field(model, field, populated, factors, table_alias, series_alias):
                dest_fields.append(SQL.identifier(field.name))
                src_fields.append(src)
    # Update char/text fields for existing rows, to allow re-entrance
    if update_fields:
        query = SQL('UPDATE %(table)s SET (%(src_columns)s) = ROW(%(dest_columns)s)',
                    table=SQL.identifier(model._table),
                    src_columns=SQL(', ').join(SQL.identifier(field.name) for field in update_fields),
                    dest_columns=SQL(', ').join(
                        get_field_variation_char(field, postfix=SQL('CHR(%s)', separator_code))
                        for field in update_fields))
        model.env.cr.execute(query)
    query = SQL("""
        INSERT INTO %(table)s (%(dest_columns)s)
        SELECT %(src_columns)s FROM %(table)s %(table_alias)s,
        GENERATE_SERIES(1, %(factor)s) %(series_alias)s
    """, table=SQL.identifier(model._table), factor=factors[model],
         dest_columns=SQL(', ').join(dest_fields), src_columns=SQL(', ').join(src_fields),
         table_alias=SQL.identifier(table_alias), series_alias=SQL.identifier(series_alias))
    model.env.cr.execute(query)
    # normally copying the 'id' will set the model entry in the populated dict,
    # but for the case of a table with no 'id' (ex: Many2many), we add manually,
    # by reading the key and having the defaultdict do the insertion, with a default value of 0
    if populated[model]:
        # in case we populated a model with an 'id', we update the sequence
        update_sequence(model)