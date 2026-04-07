def test_warning_when_unique_true_on_fk(self):
        class Foo(models.Model):
            pass

        class FKUniqueTrue(models.Model):
            fk_field = models.ForeignKey(Foo, models.CASCADE, unique=True)

        model = FKUniqueTrue()
        expected_warnings = [
            checks.Warning(
                "Setting unique=True on a ForeignKey has the same effect as using a "
                "OneToOneField.",
                hint=(
                    "ForeignKey(unique=True) is usually better served by a "
                    "OneToOneField."
                ),
                obj=FKUniqueTrue.fk_field.field,
                id="fields.W342",
            )
        ]
        warnings = model.check()
        self.assertEqual(warnings, expected_warnings)