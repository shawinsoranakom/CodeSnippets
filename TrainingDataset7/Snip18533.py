def test_datetime_trunc_sql(self):
        with self.assertRaisesMessage(
            NotImplementedError, self.may_require_msg % "datetime_trunc_sql"
        ):
            self.ops.datetime_trunc_sql(None, None, None, None)