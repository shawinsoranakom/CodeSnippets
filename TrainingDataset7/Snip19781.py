def test_name(self):
        constraints = get_constraints(Product._meta.db_table)
        for expected_name in (
            "price_gt_discounted_price",
            "constraints_product_price_gt_0",
        ):
            with self.subTest(expected_name):
                self.assertIn(expected_name, constraints)