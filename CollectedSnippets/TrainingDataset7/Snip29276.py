def test_set_reverse_on_unsaved_object(self):
        """
        Writing to the reverse relation on an unsaved object
        is impossible too.
        """
        p = Place()
        b = UndergroundBar.objects.create()

        # Assigning a reverse relation on an unsaved object is allowed.
        p.undergroundbar = b

        # However saving the object is not allowed.
        msg = (
            "save() prohibited to prevent data loss due to unsaved related object "
            "'place'."
        )
        with self.assertNumQueries(0):
            with self.assertRaisesMessage(ValueError, msg):
                b.save()