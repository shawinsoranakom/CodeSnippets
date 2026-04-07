def test_auto_created_through_model(self):
        class OtherModel(models.Model):
            pass

        class M2MModel(models.Model):
            many_to_many_rel = models.ManyToManyField(OtherModel)

        class O2OModel(models.Model):
            one_to_one_rel = models.OneToOneField(
                "invalid_models_tests.M2MModel_many_to_many_rel",
                on_delete=models.CASCADE,
            )

        field = O2OModel._meta.get_field("one_to_one_rel")
        self.assertEqual(field.check(from_model=O2OModel), [])