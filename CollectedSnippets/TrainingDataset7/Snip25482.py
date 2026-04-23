def test_valid_default_case(self):
        class Model(models.Model):
            field = models.FileField()

        self.assertEqual(Model._meta.get_field("field").check(), [])