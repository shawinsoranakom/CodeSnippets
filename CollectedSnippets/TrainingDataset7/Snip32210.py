def test_valid_sep(self):
        separators = ["/", "*sep*", ","]
        for sep in separators:
            signer = signing.Signer(key="predictable-secret", sep=sep)
            self.assertEqual(
                "foo%sjZQoX_FtSO70jX9HLRGg2A_2s4kdDBxz1QoO_OpEQb0" % sep,
                signer.sign("foo"),
            )