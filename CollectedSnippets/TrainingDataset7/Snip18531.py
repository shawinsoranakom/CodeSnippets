def test_date_trunc_sql(self):
        with self.assertRaisesMessage(
            NotImplementedError, self.may_require_msg % "date_trunc_sql"
        ):
            self.ops.date_trunc_sql(None, None, None)