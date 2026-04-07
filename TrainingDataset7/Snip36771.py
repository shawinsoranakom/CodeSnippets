def test_full_clean_with_unique_constraints(self):
        UniqueConstraintProduct.objects.create(name="product", color="yellow", rank=1)
        tests = [
            UniqueConstraintProduct(name="product", color="yellow", rank=1),
            # Child model.
            ChildUniqueConstraintProduct(name="product", color="yellow", rank=1),
        ]
        for product in tests:
            with self.subTest(model=product.__class__.__name__):
                with self.assertRaises(ValidationError) as cm:
                    product.full_clean()
                self.assertEqual(
                    cm.exception.message_dict,
                    {
                        "__all__": [
                            "Unique constraint product with this Name and Color "
                            "already exists."
                        ],
                        "rank": [
                            "Unique constraint product with this Rank already exists."
                        ],
                    },
                )