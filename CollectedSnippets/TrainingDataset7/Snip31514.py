def delete_schema():
            with connection.cursor() as cursor:
                cursor.execute("DROP SCHEMA django_schema_tests CASCADE")