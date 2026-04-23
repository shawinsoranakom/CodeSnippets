def test_abstract_fk_related_name(self):
        related_name = "%(app_label)s_%(class)s_references"

        class Referenced(models.Model):
            class Meta:
                app_label = "model_inheritance"

        class AbstractReferent(models.Model):
            reference = models.ForeignKey(
                Referenced, models.CASCADE, related_name=related_name
            )

            class Meta:
                app_label = "model_inheritance"
                abstract = True

        class Referent(AbstractReferent):
            class Meta:
                app_label = "model_inheritance"

        LocalReferent = Referent

        class Referent(AbstractReferent):
            class Meta:
                app_label = "tests"

        ForeignReferent = Referent

        self.assertFalse(hasattr(Referenced, related_name))
        self.assertIs(
            Referenced.model_inheritance_referent_references.field.model, LocalReferent
        )
        self.assertIs(Referenced.tests_referent_references.field.model, ForeignReferent)