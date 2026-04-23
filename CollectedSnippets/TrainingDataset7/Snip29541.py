def test_range_fields(self):
        class RangeFieldsModel(PostgreSQLModel):
            int_range = IntegerRangeField()
            bigint_range = BigIntegerRangeField()
            decimal_range = DecimalRangeField()
            datetime_range = DateTimeRangeField()
            date_range = DateRangeField()

        expected_errors = [
            self._make_error(field, field.__class__.__name__)
            for field in [
                RangeFieldsModel._meta.get_field("int_range"),
                RangeFieldsModel._meta.get_field("bigint_range"),
                RangeFieldsModel._meta.get_field("decimal_range"),
                RangeFieldsModel._meta.get_field("datetime_range"),
                RangeFieldsModel._meta.get_field("date_range"),
            ]
        ]
        self.assert_model_check_errors(RangeFieldsModel, expected_errors)