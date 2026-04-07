def test_datetime_extract_sql(self):
        with self.assertRaisesMessage(
            NotImplementedError, self.may_require_msg % "datetime_extract_sql"
        ):
            self.ops.datetime_extract_sql(None, None, None, None)