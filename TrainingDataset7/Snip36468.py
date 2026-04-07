def test_get_func_full_args_no_arguments(self):
        self.assertEqual(inspect.get_func_full_args(Person.no_arguments), [])
        self.assertEqual(inspect.get_func_full_args(Person().no_arguments), [])