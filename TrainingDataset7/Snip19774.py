def test_repr(self):
        constraint = models.CheckConstraint(
            condition=models.Q(price__gt=models.F("discounted_price")),
            name="price_gt_discounted_price",
        )
        self.assertEqual(
            repr(constraint),
            "<CheckConstraint: condition=(AND: ('price__gt', F(discounted_price))) "
            "name='price_gt_discounted_price'>",
        )