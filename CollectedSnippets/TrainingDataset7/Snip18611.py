def test_order_of_nls_parameters(self):
        """
        An 'almost right' datetime works with configured NLS parameters
        (#18465).
        """
        suffix = connection.features.bare_select_suffix
        with connection.cursor() as cursor:
            query = f"SELECT 1{suffix} WHERE '1936-12-29 00:00' < SYSDATE"
            # The query succeeds without errors - pre #18465 this
            # wasn't the case.
            cursor.execute(query)
            self.assertEqual(cursor.fetchone()[0], 1)