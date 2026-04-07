def test_integerchoices_functional_api(self):
        Place = models.IntegerChoices("Place", "FIRST SECOND THIRD")
        self.assertEqual(Place.labels, ["First", "Second", "Third"])
        self.assertEqual(Place.values, [1, 2, 3])
        self.assertEqual(Place.names, ["FIRST", "SECOND", "THIRD"])