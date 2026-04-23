def test_parent_child_one_to_one_link_on_nonrelated_objects(self):
        # This won't work because the Demon Dogs restaurant is not an Italian
        # restaurant.
        with self.assertRaises(ItalianRestaurant.DoesNotExist):
            Place.objects.get(name="Demon Dogs").restaurant.italianrestaurant