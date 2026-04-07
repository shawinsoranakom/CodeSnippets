def test_change_readonly_in_other_timezone(self):
        t = Timestamp.objects.create()
        with timezone.override(ICT):
            response = self.client.get(
                reverse("admin_tz:timezones_timestamp_change", args=(t.pk,))
            )
        self.assertContains(response, t.created.astimezone(ICT).isoformat())