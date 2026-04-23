def test_correct_generic_ip_passes(self):
        giptm = GenericIPAddressTestModel(generic_ip="1.2.3.4")
        self.assertIsNone(giptm.full_clean())
        giptm = GenericIPAddressTestModel(generic_ip=" 1.2.3.4 ")
        self.assertIsNone(giptm.full_clean())
        giptm = GenericIPAddressTestModel(generic_ip="1.2.3.4\n")
        self.assertIsNone(giptm.full_clean())
        giptm = GenericIPAddressTestModel(generic_ip="2001::2")
        self.assertIsNone(giptm.full_clean())