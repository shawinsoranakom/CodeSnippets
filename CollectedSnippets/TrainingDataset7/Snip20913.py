def test_tuple_of_decorators(self):
        """
        @method_decorator can accept a tuple of decorators.
        """

        def add_question_mark(func):
            def _wrapper(*args, **kwargs):
                return func(*args, **kwargs) + "?"

            return _wrapper

        def add_exclamation_mark(func):
            def _wrapper(*args, **kwargs):
                return func(*args, **kwargs) + "!"

            return _wrapper

        # The order should be consistent with the usual order in which
        # decorators are applied, e.g.
        #    @add_exclamation_mark
        #    @add_question_mark
        #    def func():
        #        ...
        decorators = (add_exclamation_mark, add_question_mark)

        @method_decorator(decorators, name="method")
        class TestFirst:
            def method(self):
                return "hello world"

        class TestSecond:
            @method_decorator(decorators)
            def method(self):
                return "hello world"

        self.assertEqual(TestFirst().method(), "hello world?!")
        self.assertEqual(TestSecond().method(), "hello world?!")