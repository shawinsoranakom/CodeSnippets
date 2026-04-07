def test_valid_case(self):
        class Model(models.Model):
            field = models.FileField(upload_to="somewhere")

        field = Model._meta.get_field("field")
        self.assertEqual(field.check(), [])