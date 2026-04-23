def test_abstract_model_app_relative_foreign_key(self):
        class AbstractReferent(models.Model):
            reference = models.ForeignKey("Referred", on_delete=models.CASCADE)

            class Meta:
                app_label = "model_fields"
                abstract = True

        def assert_app_model_resolved(label):
            class Referred(models.Model):
                class Meta:
                    app_label = label

            class ConcreteReferent(AbstractReferent):
                class Meta:
                    app_label = label

            self.assertEqual(
                ConcreteReferent._meta.get_field("reference").related_model, Referred
            )

        assert_app_model_resolved("model_fields")
        assert_app_model_resolved("tests")