def test_error_dict_copy(self):
        e = ErrorDict()
        e["__all__"] = ErrorList(
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

        e_deepcopy = copy.deepcopy(e)
        self.assertEqual(e, e_deepcopy)