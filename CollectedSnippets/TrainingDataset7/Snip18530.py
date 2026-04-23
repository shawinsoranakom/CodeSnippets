def test_time_extract_sql(self):
        with self.assertRaisesMessage(
            NotImplementedError, self.may_require_msg % "date_extract_sql"
        ):
            self.ops.time_extract_sql(None, None, None)