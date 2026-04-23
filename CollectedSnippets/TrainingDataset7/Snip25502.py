def test_valid_default(self):
        class Model(models.Model):
            field = models.JSONField(default=dict)

        self.assertEqual(Model._meta.get_field("field").check(), [])