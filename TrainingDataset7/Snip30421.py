def test_invalid_option_names(self):
        qs = Tag.objects.filter(name="test")
        tests = [
            'opt"ion',
            "o'ption",
            "op`tion",
            "opti on",
            "option--",
            "optio\tn",
            "o\nption",
            "option;",
            "你 好",
            # [] are used by MSSQL.
            "option[",
            "option]",
        ]
        for invalid_option in tests:
            with self.subTest(invalid_option):
                msg = f"Invalid option name: {invalid_option!r}"
                with self.assertRaisesMessage(ValueError, msg):
                    qs.explain(**{invalid_option: True})