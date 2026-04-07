def test_modelstate_get_field_no_order_wrt_order_field(self):
        new_apps = Apps()

        class HistoricalRecord(models.Model):
            _order = models.PositiveSmallIntegerField()

            class Meta:
                app_label = "migrations"
                apps = new_apps

        model_state = ModelState.from_model(HistoricalRecord)
        order_field = model_state.get_field("_order")
        self.assertIsNone(order_field.related_model)
        self.assertIsInstance(order_field, models.PositiveSmallIntegerField)