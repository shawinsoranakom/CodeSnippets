def test_regression_7110(self):
        """
        Regression test for bug #7110.

        When using select_related(), we must query the
        Device and Building tables using two different aliases (each) in order
        to differentiate the start and end Connection fields. The net result is
        that both the "connections = ..." queries here should give the same
        results without pulling in more than the absolute minimum number of
        tables (history has shown that it's easy to make a mistake in the
        implementation and include some unnecessary bonus joins).
        """

        b = Building.objects.create(name="101")
        dev1 = Device.objects.create(name="router", building=b)
        dev2 = Device.objects.create(name="switch", building=b)
        dev3 = Device.objects.create(name="server", building=b)
        port1 = Port.objects.create(port_number="4", device=dev1)
        port2 = Port.objects.create(port_number="7", device=dev2)
        port3 = Port.objects.create(port_number="1", device=dev3)
        c1 = Connection.objects.create(start=port1, end=port2)
        c2 = Connection.objects.create(start=port2, end=port3)

        connections = Connection.objects.filter(
            start__device__building=b, end__device__building=b
        ).order_by("id")
        self.assertEqual(
            [(c.id, str(c.start), str(c.end)) for c in connections],
            [(c1.id, "router/4", "switch/7"), (c2.id, "switch/7", "server/1")],
        )

        connections = (
            Connection.objects.filter(
                start__device__building=b, end__device__building=b
            )
            .select_related()
            .order_by("id")
        )
        self.assertEqual(
            [(c.id, str(c.start), str(c.end)) for c in connections],
            [(c1.id, "router/4", "switch/7"), (c2.id, "switch/7", "server/1")],
        )

        # This final query should only have seven tables (port, device and
        # building twice each, plus connection once). Thus, 6 joins plus the
        # FROM table.
        self.assertEqual(str(connections.query).count(" JOIN "), 6)