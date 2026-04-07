def get_test_cases_for_test_get_elided_page_range(self):
        ELLIPSIS = Paginator.ELLIPSIS
        return [
            # on_each_side=2, on_ends=1
            (1, 2, 1, [1, 2, 3, ELLIPSIS, 50]),
            (4, 2, 1, [1, 2, 3, 4, 5, 6, ELLIPSIS, 50]),
            (5, 2, 1, [1, 2, 3, 4, 5, 6, 7, ELLIPSIS, 50]),
            (6, 2, 1, [1, ELLIPSIS, 4, 5, 6, 7, 8, ELLIPSIS, 50]),
            (45, 2, 1, [1, ELLIPSIS, 43, 44, 45, 46, 47, ELLIPSIS, 50]),
            (46, 2, 1, [1, ELLIPSIS, 44, 45, 46, 47, 48, 49, 50]),
            (47, 2, 1, [1, ELLIPSIS, 45, 46, 47, 48, 49, 50]),
            (50, 2, 1, [1, ELLIPSIS, 48, 49, 50]),
            # on_each_side=1, on_ends=3
            (1, 1, 3, [1, 2, ELLIPSIS, 48, 49, 50]),
            (5, 1, 3, [1, 2, 3, 4, 5, 6, ELLIPSIS, 48, 49, 50]),
            (6, 1, 3, [1, 2, 3, 4, 5, 6, 7, ELLIPSIS, 48, 49, 50]),
            (7, 1, 3, [1, 2, 3, ELLIPSIS, 6, 7, 8, ELLIPSIS, 48, 49, 50]),
            (44, 1, 3, [1, 2, 3, ELLIPSIS, 43, 44, 45, ELLIPSIS, 48, 49, 50]),
            (45, 1, 3, [1, 2, 3, ELLIPSIS, 44, 45, 46, 47, 48, 49, 50]),
            (46, 1, 3, [1, 2, 3, ELLIPSIS, 45, 46, 47, 48, 49, 50]),
            (50, 1, 3, [1, 2, 3, ELLIPSIS, 49, 50]),
            # on_each_side=4, on_ends=0
            (1, 4, 0, [1, 2, 3, 4, 5, ELLIPSIS]),
            (5, 4, 0, [1, 2, 3, 4, 5, 6, 7, 8, 9, ELLIPSIS]),
            (6, 4, 0, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, ELLIPSIS]),
            (7, 4, 0, [ELLIPSIS, 3, 4, 5, 6, 7, 8, 9, 10, 11, ELLIPSIS]),
            (44, 4, 0, [ELLIPSIS, 40, 41, 42, 43, 44, 45, 46, 47, 48, ELLIPSIS]),
            (45, 4, 0, [ELLIPSIS, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50]),
            (46, 4, 0, [ELLIPSIS, 42, 43, 44, 45, 46, 47, 48, 49, 50]),
            (50, 4, 0, [ELLIPSIS, 46, 47, 48, 49, 50]),
            # on_each_side=0, on_ends=1
            (1, 0, 1, [1, ELLIPSIS, 50]),
            (2, 0, 1, [1, 2, ELLIPSIS, 50]),
            (3, 0, 1, [1, 2, 3, ELLIPSIS, 50]),
            (4, 0, 1, [1, ELLIPSIS, 4, ELLIPSIS, 50]),
            (47, 0, 1, [1, ELLIPSIS, 47, ELLIPSIS, 50]),
            (48, 0, 1, [1, ELLIPSIS, 48, 49, 50]),
            (49, 0, 1, [1, ELLIPSIS, 49, 50]),
            (50, 0, 1, [1, ELLIPSIS, 50]),
            # on_each_side=0, on_ends=0
            (1, 0, 0, [1, ELLIPSIS]),
            (2, 0, 0, [1, 2, ELLIPSIS]),
            (3, 0, 0, [ELLIPSIS, 3, ELLIPSIS]),
            (48, 0, 0, [ELLIPSIS, 48, ELLIPSIS]),
            (49, 0, 0, [ELLIPSIS, 49, 50]),
            (50, 0, 0, [ELLIPSIS, 50]),
        ]