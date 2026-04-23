def test_multiple_invalid_ip_raises_error(self):
        giptm = GenericIPAddressTestModel(
            v6_ip="1.2.3.4", v4_ip="::ffff:10.10.10.10", generic_ip="fsad"
        )
        self.assertFieldFailsValidationWithMessage(
            giptm.full_clean, "v6_ip", ["Enter a valid IPv6 address."]
        )
        self.assertFieldFailsValidationWithMessage(
            giptm.full_clean, "v4_ip", ["Enter a valid IPv4 address."]
        )
        self.assertFieldFailsValidationWithMessage(
            giptm.full_clean, "generic_ip", ["Enter a valid IPv4 or IPv6 address."]
        )