def test_list_compare_polyfill(x):
        for a, b, c in [
            [(1, 2, 3), (1, 2, 3), 7.77],
            [(1, 4, 3), (1, 2, 3), 3.33],
            [(1, 2), (1, 2, 3), 5.55],
            [(1, 2, 3), (1, 2), 11.11],
            [(1, -1, 3), (1, 2, 3), 13.33],
        ]:
            if a != b:
                x = x + 1 * c
            if a == b:
                x = x + 2 * c
            if a < b:
                x = x + 4 * c
            if a > b:
                x = x + 8 * c
            if a <= b:
                x = x + 16 * c
            if a >= b:
                x = x + 32 * c
        return x