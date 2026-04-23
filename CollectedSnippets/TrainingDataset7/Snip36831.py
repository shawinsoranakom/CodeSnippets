def test_empty_generic_ip_passes(self):
        giptm = GenericIPAddressTestModel(generic_ip="")
        self.assertIsNone(giptm.full_clean())
        giptm = GenericIPAddressTestModel(generic_ip=None)
        self.assertIsNone(giptm.full_clean())