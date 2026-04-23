def test_correct_v4_ip_passes(self):
        giptm = GenericIPAddressTestModel(v4_ip="1.2.3.4")
        self.assertIsNone(giptm.full_clean())