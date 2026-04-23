def test_invalid_v6_ip_raises_error(self):
        giptm = GenericIPAddressTestModel(v6_ip="1.2.3.4")
        self.assertFailsValidation(giptm.full_clean, ["v6_ip"])
        giptm = GenericIPAddressTestModel(v6_ip="1:2")
        self.assertFailsValidation(giptm.full_clean, ["v6_ip"])