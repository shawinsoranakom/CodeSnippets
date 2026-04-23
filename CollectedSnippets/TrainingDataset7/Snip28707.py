def test_parent_child_one_to_one_link(self):
        # Since the parent and child are linked by an automatically created
        # OneToOneField, you can get from the parent to the child by using the
        # child's name.
        self.assertEqual(
            Place.objects.get(name="Demon Dogs").restaurant,
            Restaurant.objects.get(name="Demon Dogs"),
        )
        self.assertEqual(
            Place.objects.get(name="Ristorante Miron").restaurant.italianrestaurant,
            ItalianRestaurant.objects.get(name="Ristorante Miron"),
        )
        self.assertEqual(
            Restaurant.objects.get(name="Ristorante Miron").italianrestaurant,
            ItalianRestaurant.objects.get(name="Ristorante Miron"),
        )