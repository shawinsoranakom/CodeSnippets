def test_inheritance_joins(self):
        # Test for #17502 - check that filtering through two levels of
        # inheritance chain doesn't generate extra joins.
        qs = ItalianRestaurant.objects.all()
        self.assertEqual(str(qs.query).count("JOIN"), 2)
        qs = ItalianRestaurant.objects.filter(name="foo")
        self.assertEqual(str(qs.query).count("JOIN"), 2)