def test_full_clean_with_check_constraints_disabled(self):
        product = Product(price=10, discounted_price=15)
        product.full_clean(validate_constraints=False)