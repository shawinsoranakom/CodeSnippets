def test_two_m2m_through_same_model_with_different_through_fields(self):
        class Country(models.Model):
            pass

        class ShippingMethod(models.Model):
            to_countries = models.ManyToManyField(
                Country,
                through="ShippingMethodPrice",
                through_fields=("method", "to_country"),
            )
            from_countries = models.ManyToManyField(
                Country,
                through="ShippingMethodPrice",
                through_fields=("method", "from_country"),
                related_name="+",
            )

        class ShippingMethodPrice(models.Model):
            method = models.ForeignKey(ShippingMethod, models.CASCADE)
            to_country = models.ForeignKey(Country, models.CASCADE)
            from_country = models.ForeignKey(Country, models.CASCADE)

        self.assertEqual(ShippingMethod.check(), [])