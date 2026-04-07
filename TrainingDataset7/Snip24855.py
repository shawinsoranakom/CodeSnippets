def test_pickle(self):
        rawdata = 'Customer="WILE_E_COYOTE"; Path=/acme; Version=1'
        expected_output = "Set-Cookie: %s" % rawdata

        C = SimpleCookie()
        C.load(rawdata)
        self.assertEqual(C.output(), expected_output)

        for proto in range(pickle.HIGHEST_PROTOCOL + 1):
            C1 = pickle.loads(pickle.dumps(C, protocol=proto))
            self.assertEqual(C1.output(), expected_output)