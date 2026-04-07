def test_get_order_field_after_removed_order_with_respect_to_field(self):
        new_apps = Apps()

        class HistoricalRecord(models.Model):
            _order = models.PositiveSmallIntegerField()

            class Meta:
                app_label = "migrations"
                apps = new_apps

        model_state = ModelState.from_model(HistoricalRecord)
        model_state.options["order_with_respect_to"] = None
        order_field = model_state.get_field("_order")
        self.assertIsNone(order_field.related_model)
        self.assertIsInstance(order_field, models.PositiveSmallIntegerField)