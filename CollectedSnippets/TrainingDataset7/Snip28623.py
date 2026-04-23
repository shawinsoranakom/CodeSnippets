def test_init_database(self):
        """Add test data to database via formset"""
        formset = self.NormalFormset(self.data)
        self.assertTrue(formset.is_valid())
        self.assertEqual(len(formset.save()), 4)