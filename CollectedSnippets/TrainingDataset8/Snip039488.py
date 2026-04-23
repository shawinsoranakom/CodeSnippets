def test_mutate_return(self, exception):
        @st.cache
        def f():
            return [0, 1]

        r = f()

        r[0] = 1

        exception.assert_not_called()

        r2 = f()

        exception.assert_called()

        self.assertEqual(r, r2)