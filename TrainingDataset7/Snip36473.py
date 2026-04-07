def test_func_accepts_var_args_no_var_args(self):
        self.assertIs(inspect.func_accepts_var_args(Person.one_argument), False)
        self.assertIs(inspect.func_accepts_var_args(Person().one_argument), False)