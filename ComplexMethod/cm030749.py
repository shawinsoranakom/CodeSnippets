def test_issue31752(self):
        # The interpreter shouldn't crash because divmod() returns negative
        # remainder.
        class BadInt(int):
            def __mul__(self, other):
                return Prod()
            def __rmul__(self, other):
                return Prod()
            def __floordiv__(self, other):
                return Prod()
            def __rfloordiv__(self, other):
                return Prod()

        class Prod:
            def __add__(self, other):
                return Sum()
            def __radd__(self, other):
                return Sum()

        class Sum(int):
            def __divmod__(self, other):
                return divmodresult

        for divmodresult in [None, (), (0, 1, 2), (0, -1)]:
            with self.subTest(divmodresult=divmodresult):
                # The following examples should not crash.
                try:
                    timedelta(microseconds=BadInt(1))
                except TypeError:
                    pass
                try:
                    timedelta(hours=BadInt(1))
                except TypeError:
                    pass
                try:
                    timedelta(weeks=BadInt(1))
                except (TypeError, ValueError):
                    pass
                try:
                    timedelta(1) * BadInt(1)
                except (TypeError, ValueError):
                    pass
                try:
                    BadInt(1) * timedelta(1)
                except TypeError:
                    pass
                try:
                    timedelta(1) // BadInt(1)
                except TypeError:
                    pass