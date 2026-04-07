def test_encode_error(self):
        for test_case in [self, any, object(), datetime.now(), set(), Decimal("3.42")]:
            with (
                self.subTest(test_case),
                self.assertRaisesMessage(TypeError, "Unsupported type"),
            ):
                normalize_json(test_case)