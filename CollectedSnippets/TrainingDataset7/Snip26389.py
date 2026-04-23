def test_fk_instantiation_outside_model(self):
        # Regression for #12190 -- Should be able to instantiate a FK outside
        # of a model, and interrogate its related field.
        cat = models.ForeignKey(Category, models.CASCADE)
        self.assertEqual("id", cat.remote_field.get_related_field().name)