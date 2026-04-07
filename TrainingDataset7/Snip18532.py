def test_time_trunc_sql(self):
        with self.assertRaisesMessage(
            NotImplementedError, self.may_require_msg % "time_trunc_sql"
        ):
            self.ops.time_trunc_sql(None, None, None)