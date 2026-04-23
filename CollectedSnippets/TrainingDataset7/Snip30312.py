def test_filter_proxy_relation_reverse(self):
        tu = TrackerUser.objects.create(name="Contributor", status="contrib")
        ptu = ProxyTrackerUser.objects.get()
        issue = Issue.objects.create(assignee=tu)
        self.assertEqual(tu.issues.get(), issue)
        self.assertEqual(ptu.issues.get(), issue)
        self.assertSequenceEqual(TrackerUser.objects.filter(issues=issue), [tu])
        self.assertSequenceEqual(ProxyTrackerUser.objects.filter(issues=issue), [ptu])