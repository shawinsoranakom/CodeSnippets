def test_distinct_on_fields(self):
        msg = "DISTINCT ON fields is not supported by this database backend"
        with self.assertRaisesMessage(NotSupportedError, msg):
            self.ops.distinct_sql(["a", "b"], None)