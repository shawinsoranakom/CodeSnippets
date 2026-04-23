def test_error_list_copy(self):
        e = ErrorList(
            [
                ValidationError(
                    message="message %(i)s",
                    params={"i": 1},
                ),
                ValidationError(
                    message="message %(i)s",
                    params={"i": 2},
                ),
            ]
        )

        e_copy = copy.copy(e)
        self.assertEqual(e, e_copy)
        self.assertEqual(e.as_data(), e_copy.as_data())