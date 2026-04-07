def assert_app_model_resolved(label):
            class Referred(models.Model):
                class Meta:
                    app_label = label

            class Through(models.Model):
                referred = models.ForeignKey("Referred", on_delete=models.CASCADE)
                referent = models.ForeignKey(
                    "ConcreteReferent", on_delete=models.CASCADE
                )

                class Meta:
                    app_label = label

            class ConcreteReferent(AbstractReferent):
                class Meta:
                    app_label = label

            self.assertEqual(
                ConcreteReferent._meta.get_field("reference").related_model, Referred
            )
            self.assertEqual(ConcreteReferent.reference.through, Through)