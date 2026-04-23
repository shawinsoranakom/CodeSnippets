def test_hashing_broken_code(self):
        import datetime

        def a():
            return datetime.strptime("%H")

        def b():
            x = datetime.strptime("%H")
            ""
            ""
            return x

        data = [
            (a, '```\nreturn datetime.strptime("%H")\n```'),
            (b, '```\nx = datetime.strptime("%H")\n""\n""\n```'),
        ]

        for func, code_msg in data:
            exc_msg = "module 'datetime' has no attribute 'strptime'"

            with self.assertRaises(UserHashError) as ctx:
                get_hash(func)

            exc = str(ctx.exception)
            self.assertEqual(exc.find(exc_msg) >= 0, True)
            self.assertNotEqual(re.search(r"a bug in `.+` near line `\d+`", exc), None)
            self.assertEqual(exc.find(code_msg) >= 0, True)