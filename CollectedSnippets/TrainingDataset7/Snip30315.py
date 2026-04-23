def test_select_related_only(self):
        user = ProxyTrackerUser.objects.create(name="Joe Doe", status="test")
        issue = Issue.objects.create(summary="New issue", assignee=user)
        qs = Issue.objects.select_related("assignee").only("assignee__status")
        self.assertEqual(qs.get(), issue)