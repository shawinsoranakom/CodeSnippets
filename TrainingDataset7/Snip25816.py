def test_values_list_flat_empty_warning(self):
        msg = (
            "Calling values_list() with no field name and flat=True "
            "is deprecated. Pass an explicit field name instead, like "
            "'pk'."
        )
        with self.assertRaisesMessage(RemovedInDjango70Warning, msg):
            Article.objects.values_list(flat=True)