def upsert_en(model, fnames, rows, conflict):
    """ Insert or update the table with the given rows.

    :param model: recordset of the model to query
    :param fnames: list of column names
    :param rows: list of tuples, where each tuple value corresponds to a column name
    :param conflict: list of column names to put into the ON CONFLICT clause
    :return: the ids of the inserted or updated rows
    """
    # for translated fields, we can actually erase the json value, as
    # translations will be reloaded after this
    def identity(val):
        return val

    def jsonify(val):
        return Json({'en_US': val}) if val is not None else val

    wrappers = [(jsonify if model._fields[fname].translate else identity) for fname in fnames]
    values = [
        tuple(func(val) for func, val in zip(wrappers, row))
        for row in rows
    ]
    comma = SQL(", ").join
    query = SQL("""
        INSERT INTO %(table)s (%(cols)s) VALUES %(values)s
        ON CONFLICT (%(conflict)s) DO UPDATE SET (%(cols)s) = (%(excluded)s)
        RETURNING id
        """,
        table=SQL.identifier(model._table),
        cols=comma(SQL.identifier(fname) for fname in fnames),
        values=comma(values),
        conflict=comma(SQL.identifier(fname) for fname in conflict),
        excluded=comma(
            (
                SQL(
                    "COALESCE(%s, '{}'::jsonb) || EXCLUDED.%s",
                    SQL.identifier(model._table, fname),
                    SQL.identifier(fname),
                )
                if model._fields[fname].translate is True
                else SQL("EXCLUDED.%s", SQL.identifier(fname))
            )
            for fname in fnames
        ),
    )
    return [id_ for id_, in model.env.execute_query(query)]