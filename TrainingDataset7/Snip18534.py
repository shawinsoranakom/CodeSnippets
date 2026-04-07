def test_datetime_cast_date_sql(self):
        with self.assertRaisesMessage(
            NotImplementedError, self.may_require_msg % "datetime_cast_date_sql"
        ):
            self.ops.datetime_cast_date_sql(None, None, None)