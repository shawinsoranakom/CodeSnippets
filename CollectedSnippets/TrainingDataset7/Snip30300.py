def test_swappable(self):
        class SwappableModel(models.Model):
            class Meta:
                swappable = "TEST_SWAPPABLE_MODEL"

        class AlternateModel(models.Model):
            pass

        # You can't proxy a swapped model
        with self.assertRaises(TypeError):

            class ProxyModel(SwappableModel):
                class Meta:
                    proxy = True