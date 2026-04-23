def test_autocomplete_e039_unresolved_model(self):
        class UnresolvedForeignKeyModel(models.Model):
            unresolved = models.ForeignKey("missing.Model", models.CASCADE)

            class Meta:
                app_label = "modeladmin"

        class Admin(ModelAdmin):
            autocomplete_fields = ("unresolved",)

        self.assertIsInvalid(
            Admin,
            UnresolvedForeignKeyModel,
            msg=(
                'An admin for model "missing.Model" has to be registered '
                "to be referenced by Admin.autocomplete_fields."
            ),
            id="admin.E039",
            invalid_obj=Admin,
        )