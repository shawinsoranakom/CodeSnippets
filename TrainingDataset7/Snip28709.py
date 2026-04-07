def test_inherited_does_not_exist_exception(self):
        # An ItalianRestaurant which does not exist is also a Place which does
        # not exist.
        with self.assertRaises(Place.DoesNotExist):
            ItalianRestaurant.objects.get(name="The Noodle Void")