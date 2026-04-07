def test_many_to_many_to_isolate_apps_model(self):
        """
        #25723 - Referenced model registration lookup should be run against the
        field's model registry.
        """

        class OtherModel(models.Model):
            pass

        class Model(models.Model):
            m2m = models.ManyToManyField("OtherModel")

        field = Model._meta.get_field("m2m")
        self.assertEqual(field.check(from_model=Model), [])