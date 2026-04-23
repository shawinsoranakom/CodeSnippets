def test_save_load(self):
        instance = GenericIPAddress.objects.create(ip="::1")
        loaded = GenericIPAddress.objects.get()
        self.assertEqual(loaded.ip, instance.ip)