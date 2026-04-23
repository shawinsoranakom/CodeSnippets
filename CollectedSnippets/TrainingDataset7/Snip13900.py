def _reset_sequences(db_name):
        conn = connections[db_name]
        if conn.features.supports_sequence_reset:
            sql_list = conn.ops.sequence_reset_by_name_sql(
                no_style(), conn.introspection.sequence_list()
            )
            if sql_list:
                with transaction.atomic(using=db_name):
                    with conn.cursor() as cursor:
                        for sql in sql_list:
                            cursor.execute(sql)