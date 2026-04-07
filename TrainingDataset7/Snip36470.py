def test_get_func_full_args_all_arguments_method(self):
        arguments = [
            ("name",),
            ("address", "home"),
            ("age", 25),
            ("*args",),
            ("**kwargs",),
        ]
        self.assertEqual(inspect.get_func_full_args(Person.all_kinds), arguments)
        self.assertEqual(inspect.get_func_full_args(Person().all_kinds), arguments)