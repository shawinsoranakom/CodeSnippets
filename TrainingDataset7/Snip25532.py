def test_foreign_key_to_isolate_apps_model(self):
        """
        #25723 - Referenced model registration lookup should be run against the
        field's model registry.
        """

        class OtherModel(models.Model):
            pass

        class Model(models.Model):
            foreign_key = models.ForeignKey("OtherModel", models.CASCADE)

        field = Model._meta.get_field("foreign_key")
        self.assertEqual(field.check(from_model=Model), [])