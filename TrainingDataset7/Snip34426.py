def test_filter_args_count(self):
        parser = Parser("")
        register = Library()

        @register.filter
        def no_arguments(value):
            pass

        @register.filter
        def one_argument(value, arg):
            pass

        @register.filter
        def one_opt_argument(value, arg=False):
            pass

        @register.filter
        def two_arguments(value, arg, arg2):
            pass

        @register.filter
        def two_one_opt_arg(value, arg, arg2=False):
            pass

        parser.add_library(register)
        for expr in (
            '1|no_arguments:"1"',
            "1|two_arguments",
            '1|two_arguments:"1"',
            "1|two_one_opt_arg",
        ):
            with self.assertRaises(TemplateSyntaxError):
                FilterExpression(expr, parser)
        for expr in (
            # Correct number of arguments
            "1|no_arguments",
            '1|one_argument:"1"',
            # One optional
            "1|one_opt_argument",
            '1|one_opt_argument:"1"',
            # Not supplying all
            '1|two_one_opt_arg:"1"',
        ):
            FilterExpression(expr, parser)