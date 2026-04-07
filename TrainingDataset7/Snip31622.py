def test_regression_22508(self):
        building = Building.objects.create(name="101")
        device = Device.objects.create(name="router", building=building)
        Port.objects.create(port_number="1", device=device)

        device = Device.objects.get()
        port = device.port_set.select_related("device__building").get()
        with self.assertNumQueries(0):
            port.device.building