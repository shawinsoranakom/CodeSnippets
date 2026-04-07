def test_change_readonly(self):
        t = Timestamp.objects.create()
        response = self.client.get(
            reverse("admin_tz:timezones_timestamp_change", args=(t.pk,))
        )
        self.assertContains(response, t.created.astimezone(EAT).isoformat())