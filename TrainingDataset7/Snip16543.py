def test_ordered_inline(self):
        """
        An inline with an editable ordering fields is updated correctly.
        """
        # Create some objects with an initial ordering
        Category.objects.create(id=1, order=1, collector=self.collector)
        Category.objects.create(id=2, order=2, collector=self.collector)
        Category.objects.create(id=3, order=0, collector=self.collector)
        Category.objects.create(id=4, order=0, collector=self.collector)

        # NB: The order values must be changed so that the items are reordered.
        self.post_data.update(
            {
                "name": "Frederick Clegg",
                "category_set-TOTAL_FORMS": "7",
                "category_set-INITIAL_FORMS": "4",
                "category_set-MAX_NUM_FORMS": "0",
                "category_set-0-order": "14",
                "category_set-0-id": "1",
                "category_set-0-collector": "1",
                "category_set-1-order": "13",
                "category_set-1-id": "2",
                "category_set-1-collector": "1",
                "category_set-2-order": "1",
                "category_set-2-id": "3",
                "category_set-2-collector": "1",
                "category_set-3-order": "0",
                "category_set-3-id": "4",
                "category_set-3-collector": "1",
                "category_set-4-order": "",
                "category_set-4-id": "",
                "category_set-4-collector": "1",
                "category_set-5-order": "",
                "category_set-5-id": "",
                "category_set-5-collector": "1",
                "category_set-6-order": "",
                "category_set-6-id": "",
                "category_set-6-collector": "1",
            }
        )
        collector_url = reverse(
            "admin:admin_views_collector_change", args=(self.collector.pk,)
        )
        response = self.client.post(collector_url, self.post_data)
        # Successful post will redirect
        self.assertEqual(response.status_code, 302)

        # The order values have been applied to the right objects
        self.assertEqual(self.collector.category_set.count(), 4)
        self.assertEqual(Category.objects.get(id=1).order, 14)
        self.assertEqual(Category.objects.get(id=2).order, 13)
        self.assertEqual(Category.objects.get(id=3).order, 1)
        self.assertEqual(Category.objects.get(id=4).order, 0)