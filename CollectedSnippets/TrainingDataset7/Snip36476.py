def test_func_accepts_kwargs(self):
        self.assertIs(inspect.func_accepts_kwargs(Person.just_args), False)
        self.assertIs(inspect.func_accepts_kwargs(Person().just_args), False)
        self.assertIs(inspect.func_accepts_kwargs(Person.all_kinds), True)
        self.assertIs(inspect.func_accepts_kwargs(Person().just_args), False)