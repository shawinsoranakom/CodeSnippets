def test_add_generated_field(self):
        class GeneratedFieldOutputFieldModel(Model):
            price = DecimalField(max_digits=7, decimal_places=2)
            vat_price = GeneratedField(
                expression=Round(F("price") * Value(Decimal("1.22")), 2),
                db_persist=True,
                output_field=DecimalField(max_digits=8, decimal_places=2),
            )

            class Meta:
                app_label = "schema"

        with connection.schema_editor() as editor:
            editor.create_model(GeneratedFieldOutputFieldModel)