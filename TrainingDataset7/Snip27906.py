def test_get_col(self):
        class Square(Model):
            side = IntegerField()
            area = GeneratedField(
                expression=F("side") * F("side"),
                output_field=IntegerField(),
                db_persist=True,
            )

        field = Square._meta.get_field("area")

        col = field.get_col("alias")
        self.assertIsInstance(col.output_field, IntegerField)

        col = field.get_col("alias", field)
        self.assertIsInstance(col.output_field, IntegerField)

        class FloatSquare(Model):
            side = IntegerField()
            area = GeneratedField(
                expression=F("side") * F("side"),
                db_persist=True,
                output_field=FloatField(),
            )

        field = FloatSquare._meta.get_field("area")

        col = field.get_col("alias")
        self.assertIsInstance(col.output_field, FloatField)

        col = field.get_col("alias", field)
        self.assertIsInstance(col.output_field, FloatField)