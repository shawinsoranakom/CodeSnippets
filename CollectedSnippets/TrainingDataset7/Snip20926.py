async def test_wrapper_assignments(self):
        """@method_decorator preserves wrapper assignments."""
        func_data = {}

        def decorator(func):
            @wraps(func)
            async def inner(*args, **kwargs):
                func_data["func_name"] = getattr(func, "__name__", None)
                func_data["func_module"] = getattr(func, "__module__", None)
                return await func(*args, **kwargs)

            return inner

        class Test:
            @method_decorator(decorator)
            async def method(self):
                return "tests"

        await Test().method()
        expected = {"func_name": "method", "func_module": "decorators.tests"}
        self.assertEqual(func_data, expected)