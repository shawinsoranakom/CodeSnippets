def test_get_func_full_args_one_argument(self):
        self.assertEqual(
            inspect.get_func_full_args(Person.one_argument), [("something",)]
        )
        self.assertEqual(
            inspect.get_func_full_args(Person().one_argument),
            [("something",)],
        )