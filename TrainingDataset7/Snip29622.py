def test_exact_ip_addresses(self):
        self.assertSequenceEqual(
            OtherTypesArrayModel.objects.filter(ips=self.ips), self.objs
        )