def test_valid_callable_default(self):
        def callable_default():
            return {"it": "works"}

        class Model(models.Model):
            field = models.JSONField(default=callable_default)

        self.assertEqual(Model._meta.get_field("field").check(), [])