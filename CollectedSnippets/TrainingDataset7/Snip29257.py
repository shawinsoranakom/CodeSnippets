def test_unsaved_object(self):
        """
        #10811 -- Assigning an unsaved object to a OneToOneField
        should raise an exception.
        """
        place = Place(name="User", address="London")
        with self.assertRaises(Restaurant.DoesNotExist):
            place.restaurant
        msg = (
            "save() prohibited to prevent data loss due to unsaved related object "
            "'place'."
        )
        with self.assertRaisesMessage(ValueError, msg):
            Restaurant.objects.create(
                place=place, serves_hot_dogs=True, serves_pizza=False
            )
        # place should not cache restaurant
        with self.assertRaises(Restaurant.DoesNotExist):
            place.restaurant