def test_prefetch_related_objects_with_various_iterables(self):
        book = self.book1

        class MyIterable:
            def __iter__(self):
                yield book

        cases = {
            "set": {book},
            "tuple": (book,),
            "dict_values": {"a": book}.values(),
            "frozenset": frozenset([book]),
            "deque": deque([book]),
            "custom iterator": MyIterable(),
        }
        for case_type, case in cases.items():
            with self.subTest(case=case_type):
                # Clear the prefetch cache.
                book._prefetched_objects_cache = {}
                with self.assertNumQueries(1):
                    prefetch_related_objects(case, "authors")
                with self.assertNumQueries(0):
                    self.assertCountEqual(
                        book.authors.all(), [self.author1, self.author2, self.author3]
                    )