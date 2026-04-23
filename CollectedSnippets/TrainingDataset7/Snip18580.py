def get_isolation_level(connection):
        with connection.cursor() as cursor:
            cursor.execute(
                "SHOW VARIABLES "
                "WHERE variable_name IN ('transaction_isolation', 'tx_isolation')"
            )
            return cursor.fetchone()[1].replace("-", " ")