def test_valid_default_value(self):
        class Model(models.Model):
            field1 = models.BinaryField(default=b"test")
            field2 = models.BinaryField(default=None)

        for field_name in ("field1", "field2"):
            field = Model._meta.get_field(field_name)
            self.assertEqual(field.check(), [])