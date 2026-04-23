def test_iter_test_cases_string_input(self):
        msg = (
            "Test 'a' must be a test case or test suite not string (was found "
            "in 'abc')."
        )
        with self.assertRaisesMessage(TypeError, msg):
            list(iter_test_cases("abc"))