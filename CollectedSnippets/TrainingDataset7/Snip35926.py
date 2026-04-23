def test_unhandled_exceptions(self):
        cases = [
            StringIO("Hello world"),
            TextIOWrapper(BytesIO(b"Hello world")),
        ]
        for out in cases:
            with self.subTest(out=out):
                wrapper = OutputWrapper(out)
                out.close()

                unraisable_exceptions = []

                def unraisablehook(unraisable):
                    unraisable_exceptions.append(unraisable)
                    sys.__unraisablehook__(unraisable)

                with mock.patch.object(sys, "unraisablehook", unraisablehook):
                    del wrapper

                self.assertEqual(unraisable_exceptions, [])