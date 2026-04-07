def test_property_resolver(self):
        user = User()
        dict_data = {
            "a": {
                "b1": {"c": "result1"},
                "b2": user,
                "b3": {"0": "result2"},
                "b4": [0, 1, 2],
            }
        }
        list_data = ["a", "b", "c"]
        tests = [
            ("a.b1.c", dict_data, "result1"),
            ("a.b2.password", dict_data, "abc"),
            ("a.b2.test_property", dict_data, "cde"),
            # The method should not get called.
            ("a.b2.test_method", dict_data, user.test_method),
            ("a.b3.0", dict_data, "result2"),
            (0, list_data, "a"),
        ]
        for arg, data, expected_value in tests:
            with self.subTest(arg=arg):
                self.assertEqual(_property_resolver(arg)(data), expected_value)
        # Invalid lookups.
        fail_tests = [
            ("a.b1.d", dict_data, AttributeError),
            ("a.b2.password.0", dict_data, AttributeError),
            ("a.b2._private", dict_data, AttributeError),
            ("a.b4.0", dict_data, AttributeError),
            ("a", list_data, AttributeError),
            ("0", list_data, TypeError),
            (4, list_data, IndexError),
        ]
        for arg, data, expected_exception in fail_tests:
            with self.subTest(arg=arg):
                with self.assertRaises(expected_exception):
                    _property_resolver(arg)(data)