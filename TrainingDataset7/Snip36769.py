def test_full_clean_with_check_constraints_on_child_model(self):
        product = ChildProduct(price=10, discounted_price=15)
        with self.assertRaises(ValidationError) as cm:
            product.full_clean()
        self.assertEqual(
            cm.exception.message_dict,
            {
                "__all__": [
                    "Constraint “price_gt_discounted_price_validation” is violated."
                ]
            },
        )