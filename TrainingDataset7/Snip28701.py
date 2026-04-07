def test_full_clean(self):
        restaurant = Restaurant.objects.create()
        with self.assertNumQueries(0), self.assertRaises(ValidationError):
            restaurant.full_clean()