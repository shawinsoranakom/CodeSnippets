def setUp(self):
        models.DateField.register_lookup(YearTransform)
        self.addCleanup(models.DateField._unregister_lookup, YearTransform)