def test_date_extract_sql(self):
        with self.assertRaisesMessage(
            NotImplementedError, self.may_require_msg % "date_extract_sql"
        ):
            self.ops.date_extract_sql(None, None, None)