def test_lefthand_bitwise_xor_not_supported(self):
        msg = "Bitwise XOR is not supported in Oracle."
        with self.assertRaisesMessage(NotSupportedError, msg):
            Number.objects.update(integer=F("integer").bitxor(48))