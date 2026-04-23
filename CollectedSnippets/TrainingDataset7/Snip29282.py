def test_update_or_create_reverse_o2o_error(self):
        msg = "The following fields do not exist in this model: restaurant"
        r2 = Restaurant.objects.create(
            place=self.p2, serves_hot_dogs=True, serves_pizza=False
        )
        with self.assertRaisesMessage(ValueError, msg):
            Place.objects.update_or_create(
                name="nonexistent", defaults={"restaurant": r2}
            )