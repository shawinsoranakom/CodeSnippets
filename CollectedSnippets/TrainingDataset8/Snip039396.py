def test_mutate_return(self, exception):
        """Mutating a memoized return value is legal, and *won't* affect
        future accessors of the data."""

        @st.experimental_memo
        def f():
            return [0, 1]

        r1 = f()

        r1[0] = 1

        r2 = f()

        exception.assert_not_called()

        self.assertEqual(r1, [1, 1])
        self.assertEqual(r2, [0, 1])