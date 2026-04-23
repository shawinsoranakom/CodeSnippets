def test_label_in_hierarchy(self):
        self.client.force_login(self.superuser)
        Event.objects.create(date=datetime(2017, 1, 1))
        response = self.client.get(reverse("admin:admin_changelist_event_changelist"))
        self.assertContains(response, "Filter by date", status_code=200)