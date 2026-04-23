def field_needs_variation(model: Model, field: Field) -> bool:
    """
    Return True/False depending on if the field needs to be varied.
    Might be necessary in the case of:
    - unique constraints
    - varying dates for better distribution
    - field will be part of _rec_name_search, therefor variety is needed for effective searches
    - field has a trigram index on it
    """
    def is_unique(model_, field_):
        """
        An unique constraint is enforced by Postgres as an unique index,
        whether it's defined as a constraint on the table, or as an manual unique index.
        Both type of constraint are present in the index catalog
        """
        query = SQL("""
        SELECT EXISTS(SELECT 1
              FROM pg_index idx
                   JOIN pg_class t ON t.oid = idx.indrelid
                   JOIN pg_class i ON i.oid = idx.indexrelid
                   JOIN pg_attribute a ON a.attnum = ANY (idx.indkey) AND a.attrelid = t.oid
              WHERE t.relname = %s  -- tablename
                AND a.attname = %s  -- column
                AND t.relnamespace = current_schema::regnamespace
                AND idx.indisunique = TRUE) AS is_unique;
        """, model_._table, field_.name)
        return model_.env.execute_query(query)[0][0]

    # Many2one fields are not considered, as a name_search would resolve it to the _rec_names_search of the related model
    in_names_search = model._rec_names_search and field.name in model._rec_names_search
    in_name = model._rec_name and field.name == model._rec_name
    if (in_name or in_names_search) and field.type != 'many2one':
        return True
    if field.type in ('date', 'datetime'):
        return True
    if field.index == 'trigram':
        return True
    return is_unique(model, field)