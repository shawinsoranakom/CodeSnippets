def check(tests, byteorder, signed=False):
            def equivalent_python(n, length, byteorder, signed=False):
                if byteorder == 'little':
                    order = range(length)
                elif byteorder == 'big':
                    order = reversed(range(length))
                return bytes((n >> i*8) & 0xff for i in order)

            for test, expected in tests.items():
                try:
                    self.assertEqual(
                        test.to_bytes(len(expected), byteorder, signed=signed),
                        expected)
                except Exception as err:
                    raise AssertionError(
                        "failed to convert {} with byteorder={} and signed={}"
                        .format(test, byteorder, signed)) from err

                # Test for all default arguments.
                if len(expected) == 1 and byteorder == 'big' and not signed:
                    try:
                        self.assertEqual(test.to_bytes(), expected)
                    except Exception as err:
                        raise AssertionError(
                            "failed to convert {} with default arguments"
                            .format(test)) from err

                try:
                    self.assertEqual(
                        equivalent_python(
                            test, len(expected), byteorder, signed=signed),
                        expected
                    )
                except Exception as err:
                    raise AssertionError(
                        "Code equivalent from docs is not equivalent for "
                        "conversion of {0} with byteorder byteorder={1} and "
                        "signed={2}".format(test, byteorder, signed)) from err