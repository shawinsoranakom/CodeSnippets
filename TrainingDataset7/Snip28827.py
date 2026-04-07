def sql_for_table(model):
    with connection.schema_editor(collect_sql=True) as editor:
        editor.create_model(model)
    return editor.collected_sql[0]