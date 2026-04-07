async def test_data_types(self):
        """All data types are ignored equally by the dummy cache."""

        def f():
            return 42

        class C:
            def m(n):
                return 24

        data = {
            "string": "this is a string",
            "int": 42,
            "list": [1, 2, 3, 4],
            "tuple": (1, 2, 3, 4),
            "dict": {"A": 1, "B": 2},
            "function": f,
            "class": C,
        }
        await cache.aset("data", data)
        self.assertIsNone(await cache.aget("data"))