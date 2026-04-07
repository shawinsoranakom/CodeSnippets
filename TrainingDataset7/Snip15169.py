def test_changelist_view_list_editable_changed_objects_uses_filter(self):
        """
        list_editable edits use a filtered queryset to limit memory usage.
        """
        a = Swallow.objects.create(origin="Swallow A", load=4, speed=1)
        Swallow.objects.create(origin="Swallow B", load=2, speed=2)
        data = {
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "2",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-uuid": str(a.pk),
            "form-0-load": "10",
            "_save": "Save",
        }
        superuser = self._create_superuser("superuser")
        self.client.force_login(superuser)
        changelist_url = reverse("admin:admin_changelist_swallow_changelist")
        with CaptureQueriesContext(connection) as context:
            response = self.client.post(changelist_url, data=data)
            self.assertEqual(response.status_code, 200)
            self.assertIn("WHERE", context.captured_queries[4]["sql"])
            self.assertIn("IN", context.captured_queries[4]["sql"])
            # Check only the first few characters since the UUID may have
            # dashes.
            self.assertIn(str(a.pk)[:8], context.captured_queries[4]["sql"])