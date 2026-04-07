def test_connect_no_is_usable_checks(self):
        new_connection = no_pool_connection()
        try:
            with mock.patch.object(new_connection, "is_usable") as is_usable:
                new_connection.connect()
            is_usable.assert_not_called()
        finally:
            new_connection.close()