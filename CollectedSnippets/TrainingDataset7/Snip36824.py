def test_invalid_generic_ip_raises_error(self):
        giptm = GenericIPAddressTestModel(generic_ip="294.4.2.1")
        self.assertFailsValidation(giptm.full_clean, ["generic_ip"])
        giptm = GenericIPAddressTestModel(generic_ip="1:2")
        self.assertFailsValidation(giptm.full_clean, ["generic_ip"])
        giptm = GenericIPAddressTestModel(generic_ip=1)
        self.assertFailsValidation(giptm.full_clean, ["generic_ip"])
        giptm = GenericIPAddressTestModel(generic_ip=lazy(lambda: 1, int))
        self.assertFailsValidation(giptm.full_clean, ["generic_ip"])