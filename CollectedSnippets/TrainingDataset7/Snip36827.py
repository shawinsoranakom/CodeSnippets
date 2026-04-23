def test_correct_v6_ip_passes(self):
        giptm = GenericIPAddressTestModel(v6_ip="2001::2")
        self.assertIsNone(giptm.full_clean())