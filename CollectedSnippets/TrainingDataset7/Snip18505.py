def test_get_table_list(self):
        msg = self.may_require_msg % "get_table_list"
        with self.assertRaisesMessage(NotImplementedError, msg):
            self.introspection.get_table_list(None)