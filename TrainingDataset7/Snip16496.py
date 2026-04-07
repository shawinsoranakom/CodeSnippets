def test_list_editable_ordering(self):
        collector = Collector.objects.create(id=1, name="Frederick Clegg")

        Category.objects.create(id=1, order=1, collector=collector)
        Category.objects.create(id=2, order=2, collector=collector)
        Category.objects.create(id=3, order=0, collector=collector)
        Category.objects.create(id=4, order=0, collector=collector)

        # NB: The order values must be changed so that the items are reordered.
        data = {
            "form-TOTAL_FORMS": "4",
            "form-INITIAL_FORMS": "4",
            "form-MAX_NUM_FORMS": "0",
            "form-0-order": "14",
            "form-0-id": "1",
            "form-0-collector": "1",
            "form-1-order": "13",
            "form-1-id": "2",
            "form-1-collector": "1",
            "form-2-order": "1",
            "form-2-id": "3",
            "form-2-collector": "1",
            "form-3-order": "0",
            "form-3-id": "4",
            "form-3-collector": "1",
            # The form processing understands this as a list_editable "Save"
            # and not an action "Go".
            "_save": "Save",
        }
        response = self.client.post(
            reverse("admin:admin_views_category_changelist"), data
        )
        # Successful post will redirect
        self.assertEqual(response.status_code, 302)

        # The order values have been applied to the right objects
        self.assertEqual(Category.objects.get(id=1).order, 14)
        self.assertEqual(Category.objects.get(id=2).order, 13)
        self.assertEqual(Category.objects.get(id=3).order, 1)
        self.assertEqual(Category.objects.get(id=4).order, 0)