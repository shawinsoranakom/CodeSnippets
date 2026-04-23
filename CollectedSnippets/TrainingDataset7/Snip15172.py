def test_ordering_from_model_meta(self):
        Swallow.objects.create(origin="Swallow A", load=4, speed=2)
        Swallow.objects.create(origin="Swallow B", load=2, speed=1)
        Swallow.objects.create(origin="Swallow C", load=5, speed=1)
        m = SwallowAdmin(Swallow, custom_site)
        request = self._mocked_authenticated_request("/swallow/?o=", self.superuser)
        changelist = m.get_changelist_instance(request)
        queryset = changelist.get_queryset(request)
        self.assertQuerySetEqual(
            queryset,
            [(1.0, 2.0), (1.0, 5.0), (2.0, 4.0)],
            lambda s: (s.speed, s.load),
        )