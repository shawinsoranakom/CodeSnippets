def test_explicit_swappable_manager(self):
        class SwappableModel(models.Model):
            objects = models.Manager()

            class Meta:
                swappable = "TEST_SWAPPABLE_MODEL"

        # Accessing the manager on a swappable model with an
        # explicit manager should raise an attribute error with a
        # helpful message
        msg = (
            "Manager isn't available; 'managers_regress.SwappableModel' "
            "has been swapped for 'managers_regress.Parent'"
        )
        with self.assertRaisesMessage(AttributeError, msg):
            SwappableModel.objects.all()