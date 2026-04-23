def test_full_clean_with_partial_unique_constraints_disabled(self):
        UniqueConstraintConditionProduct.objects.create(name="product")
        product = UniqueConstraintConditionProduct(name="product")
        product.full_clean(validate_constraints=False)