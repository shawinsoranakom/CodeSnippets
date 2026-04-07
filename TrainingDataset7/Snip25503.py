def test_valid_default_none(self):
        class Model(models.Model):
            field = models.JSONField(default=None)

        self.assertEqual(Model._meta.get_field("field").check(), [])