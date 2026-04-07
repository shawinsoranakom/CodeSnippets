def test_aggregate_arity(self):
        funcs_with_inherited_constructors = [Avg, Max, Min, Sum]
        msg = "takes exactly 1 argument (2 given)"
        for function in funcs_with_inherited_constructors:
            with (
                self.subTest(function=function),
                self.assertRaisesMessage(TypeError, msg),
            ):
                function(Value(1), Value(2))

        funcs_with_custom_constructors = [Count, StdDev, Variance]
        for function in funcs_with_custom_constructors:
            with self.subTest(function=function):
                # Extra arguments are rejected via the constructor.
                with self.assertRaises(TypeError):
                    function(Value(1), True, Value(2))
                # If the constructor is skipped, the arity check runs.
                func_instance = function(Value(1), True)
                with self.assertRaisesMessage(TypeError, msg):
                    super(function, func_instance).__init__(Value(1), Value(2))