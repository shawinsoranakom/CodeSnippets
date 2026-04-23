def test_not_shareable(self):
        okay = [
            *PICKLEABLE,
            *defs.STATELESS_FUNCTIONS,
            LAMBDA,
        ]
        ignored = [
            *TUPLES_WITHOUT_EQUALITY,
            OBJECT,
            METHOD,
            BUILTIN_METHOD,
            METHOD_WRAPPER,
        ]
        with ignore_byteswarning():
            self.assert_roundtrip_equal([
                *(o for o in NOT_SHAREABLE
                  if o in okay and o not in ignored
                  and o is not MAPPING_PROXY_EMPTY),
            ])
            self.assert_roundtrip_not_equal([
                *(o for o in NOT_SHAREABLE
                  if o in ignored and o is not MAPPING_PROXY_EMPTY),
            ])
            self.assert_not_shareable([
                *(o for o in NOT_SHAREABLE if o not in okay),
                MAPPING_PROXY_EMPTY,
            ])