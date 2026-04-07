def make_configuration_query():
            is_opening_connection = connection.connection is None
            real_ensure_connection()

            if is_opening_connection:
                # Avoid infinite recursion. Creating a cursor calls
                # ensure_connection() which is currently mocked by this method.
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1" + connection.features.bare_select_suffix)