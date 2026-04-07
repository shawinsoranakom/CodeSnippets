def test_valid_foreign_key_without_accessor(self):
        class Target(models.Model):
            # There would be a clash if Model.field installed an accessor.
            model = models.IntegerField()

        class Model(models.Model):
            field = models.ForeignKey(Target, models.CASCADE, related_name="+")

        field = Model._meta.get_field("field")
        self.assertEqual(field.check(), [])