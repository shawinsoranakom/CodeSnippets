def test_swappable_manager(self):
        class SwappableModel(models.Model):
            class Meta:
                swappable = "TEST_SWAPPABLE_MODEL"

        # Accessing the manager on a swappable model should
        # raise an attribute error with a helpful message
        msg = (
            "Manager isn't available; 'managers_regress.SwappableModel' "
            "has been swapped for 'managers_regress.Parent'"
        )
        with self.assertRaisesMessage(AttributeError, msg):
            SwappableModel.objects.all()