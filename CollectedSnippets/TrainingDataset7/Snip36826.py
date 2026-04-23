def test_invalid_v4_ip_raises_error(self):
        giptm = GenericIPAddressTestModel(v4_ip="294.4.2.1")
        self.assertFailsValidation(giptm.full_clean, ["v4_ip"])
        giptm = GenericIPAddressTestModel(v4_ip="2001::2")
        self.assertFailsValidation(giptm.full_clean, ["v4_ip"])