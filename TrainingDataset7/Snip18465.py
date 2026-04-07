def test_database_queried(self):
        wrapper = self.mock_wrapper()
        with connection.execute_wrapper(wrapper):
            with connection.cursor() as cursor:
                sql = "SELECT 17" + connection.features.bare_select_suffix
                cursor.execute(sql)
                seventeen = cursor.fetchall()
                self.assertEqual(list(seventeen), [(17,)])
            self.call_executemany(connection)