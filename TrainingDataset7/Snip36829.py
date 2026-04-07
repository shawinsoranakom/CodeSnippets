def test_v6_uniqueness_detection(self):
        # These two addresses are the same with different syntax
        giptm = GenericIPAddressTestModel(generic_ip="2001::1:0:0:0:0:2")
        giptm.save()
        giptm = GenericIPAddressTestModel(generic_ip="2001:0:1:2")
        self.assertFailsValidation(giptm.full_clean, ["generic_ip"])