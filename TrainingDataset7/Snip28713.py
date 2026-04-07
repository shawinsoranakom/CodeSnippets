def test_update_works_on_parent_and_child_models_at_once(self):
        # The update() command can update fields in parent and child classes at
        # once (although it executed multiple SQL queries to do so).
        rows = Restaurant.objects.filter(
            serves_hot_dogs=True, name__contains="D"
        ).update(name="Demon Puppies", serves_hot_dogs=False)
        self.assertEqual(rows, 1)

        r1 = Restaurant.objects.get(pk=self.restaurant.pk)
        self.assertFalse(r1.serves_hot_dogs)
        self.assertEqual(r1.name, "Demon Puppies")