def test_foreign_keys_in_parents(self):
        self.assertEqual(type(_get_foreign_key(Restaurant, Owner)), models.ForeignKey)
        self.assertEqual(
            type(_get_foreign_key(MexicanRestaurant, Owner)), models.ForeignKey
        )