def test_get_table_description(self):
        msg = self.may_require_msg % "get_table_description"
        with self.assertRaisesMessage(NotImplementedError, msg):
            self.introspection.get_table_description(None, None)