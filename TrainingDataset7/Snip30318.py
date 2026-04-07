def test_cascade_delete_proxy_model_admin_warning(self):
        """
        Test if admin gives warning about cascade deleting models referenced
        to concrete model by deleting proxy object.
        """
        tracker_user = TrackerUser.objects.all()[0]
        base_user = BaseUser.objects.all()[0]
        issue = Issue.objects.all()[0]
        with self.assertNumQueries(6):
            collector = admin.utils.NestedObjects("default")
            collector.collect(ProxyTrackerUser.objects.all())
        self.assertIn(tracker_user, collector.edges.get(None, ()))
        self.assertIn(base_user, collector.edges.get(None, ()))
        self.assertIn(issue, collector.edges.get(tracker_user, ()))