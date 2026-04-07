def test_proxy_bug(self):
        contributor = ProxyTrackerUser.objects.create(
            name="Contributor", status="contrib"
        )
        someone = BaseUser.objects.create(name="Someone")
        Bug.objects.create(
            summary="fix this",
            version="1.1beta",
            assignee=contributor,
            reporter=someone,
        )
        pcontributor = ProxyTrackerUser.objects.create(
            name="OtherContributor", status="proxy"
        )
        Improvement.objects.create(
            summary="improve that",
            version="1.1beta",
            assignee=contributor,
            reporter=pcontributor,
            associated_bug=ProxyProxyBug.objects.all()[0],
        )

        # Related field filter on proxy
        resp = ProxyBug.objects.get(version__icontains="beta")
        self.assertEqual(repr(resp), "<ProxyBug: ProxyBug:fix this>")

        # Select related + filter on proxy
        resp = ProxyBug.objects.select_related().get(version__icontains="beta")
        self.assertEqual(repr(resp), "<ProxyBug: ProxyBug:fix this>")

        # Proxy of proxy, select_related + filter
        resp = ProxyProxyBug.objects.select_related().get(version__icontains="beta")
        self.assertEqual(repr(resp), "<ProxyProxyBug: ProxyProxyBug:fix this>")

        # Select related + filter on a related proxy field
        resp = ProxyImprovement.objects.select_related().get(
            reporter__name__icontains="butor"
        )
        self.assertEqual(
            repr(resp), "<ProxyImprovement: ProxyImprovement:improve that>"
        )

        # Select related + filter on a related proxy of proxy field
        resp = ProxyImprovement.objects.select_related().get(
            associated_bug__summary__icontains="fix"
        )
        self.assertEqual(
            repr(resp), "<ProxyImprovement: ProxyImprovement:improve that>"
        )