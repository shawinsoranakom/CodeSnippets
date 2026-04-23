def test_pickle_model(self):
        """
        Test on an actual model, based on the report in #25426.
        """
        category = Category.objects.create(name="thing1")
        CategoryInfo.objects.create(category=category)
        # Test every pickle protocol available
        for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
            lazy_category = SimpleLazyObject(lambda: category)
            # Test both if we accessed a field on the model and if we didn't.
            lazy_category.categoryinfo
            lazy_category_2 = SimpleLazyObject(lambda: category)
            with warnings.catch_warnings(record=True) as recorded:
                self.assertEqual(
                    pickle.loads(pickle.dumps(lazy_category, protocol)), category
                )
                self.assertEqual(
                    pickle.loads(pickle.dumps(lazy_category_2, protocol)), category
                )
                # Assert that there were no warnings.
                self.assertEqual(len(recorded), 0)