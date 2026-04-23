def test_compare_equal(self):
        # A memoryview is equal to itself: there is no need to compare
        # individual values. This is not true for float values since they can
        # be NaN, and NaN is not equal to itself.

        def check_equal(view, is_equal):
            self.assertEqual(view == view, is_equal)
            self.assertEqual(view != view, not is_equal)

            # Comparison with a different memoryview doesn't use
            # the optimization and should give the same result.
            view2 = memoryview(view)
            self.assertEqual(view2 == view, is_equal)
            self.assertEqual(view2 != view2, not is_equal)

        # Test integer formats
        for int_format in 'bBhHiIlLqQ':
            with self.subTest(format=int_format):
                a = array.array(int_format, [1, 2, 3])
                m = memoryview(a)
                check_equal(m, True)

                if int_format in 'bB':
                    m2 = m.cast('@' + m.format)
                    check_equal(m2, True)

        # Test 'c' format
        a = array.array('B', [1, 2, 3])
        m = memoryview(a.tobytes()).cast('c')
        check_equal(m, True)

        # Test 'n' and 'N' formats
        if struct.calcsize('L') == struct.calcsize('N'):
            int_format = 'L'
        elif struct.calcsize('Q') == struct.calcsize('N'):
            int_format = 'Q'
        else:
            int_format = None
        if int_format:
            a = array.array(int_format, [1, 2, 3])
            m = memoryview(a.tobytes()).cast('N')
            check_equal(m, True)
            m = memoryview(a.tobytes()).cast('n')
            check_equal(m, True)

        # Test '?' format
        m = memoryview(b'\0\1\2').cast('?')
        check_equal(m, True)

        # Test float formats
        for float_format in 'fd':
            with self.subTest(format=float_format):
                a = array.array(float_format, [1.0, 2.0, float('nan')])
                m = memoryview(a)
                # nan is not equal to nan
                check_equal(m, False)

                a = array.array(float_format, [1.0, 2.0, 3.0])
                m = memoryview(a)
                check_equal(m, True)

        # Test complex formats
        for complex_format in 'FD':
            with self.subTest(format=complex_format):
                data = struct.pack(complex_format * 3, 1.0, 2.0, float('nan'))
                m = memoryview(data).cast(complex_format)
                # nan is not equal to nan
                check_equal(m, False)

                data = struct.pack(complex_format * 3, 1.0, 2.0, 3.0)
                m = memoryview(data).cast(complex_format)
                check_equal(m, True)