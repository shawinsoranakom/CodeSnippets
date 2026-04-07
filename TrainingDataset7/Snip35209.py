def test_ignores_connection_configuration_queries(self):
        real_ensure_connection = connection.ensure_connection
        connection.close()

        def make_configuration_query():
            is_opening_connection = connection.connection is None
            real_ensure_connection()

            if is_opening_connection:
                # Avoid infinite recursion. Creating a cursor calls
                # ensure_connection() which is currently mocked by this method.
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1" + connection.features.bare_select_suffix)

        ensure_connection = (
            "django.db.backends.base.base.BaseDatabaseWrapper.ensure_connection"
        )
        with mock.patch(ensure_connection, side_effect=make_configuration_query):
            with self.assertNumQueries(1):
                list(Car.objects.all())