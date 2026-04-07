def _test_procedure(self, procedure_sql, params, param_types, kparams=None):
        with connection.cursor() as cursor:
            cursor.execute(procedure_sql)
        # Use a new cursor because in MySQL a procedure can't be used in the
        # same cursor in which it was created.
        with connection.cursor() as cursor:
            cursor.callproc("test_procedure", params, kparams)
        with connection.schema_editor() as editor:
            editor.remove_procedure("test_procedure", param_types)