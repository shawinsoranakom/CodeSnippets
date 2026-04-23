def sql_for_index(model):
    return "\n".join(
        str(sql) for sql in connection.schema_editor()._model_indexes_sql(model)
    )