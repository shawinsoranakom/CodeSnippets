def test_cached_col(self):
        class Sum(Model):
            a = IntegerField()
            b = IntegerField()
            total = GeneratedField(
                expression=F("a") + F("b"), output_field=IntegerField(), db_persist=True
            )

        field = Sum._meta.get_field("total")
        cached_col = field.cached_col
        self.assertIs(field.get_col(Sum._meta.db_table), cached_col)
        self.assertIs(field.get_col(Sum._meta.db_table, field), cached_col)
        self.assertIsNot(field.get_col("alias"), cached_col)
        self.assertIsNot(field.get_col(Sum._meta.db_table, IntegerField()), cached_col)
        self.assertIs(cached_col.target, field)
        self.assertIsInstance(cached_col.output_field, IntegerField)