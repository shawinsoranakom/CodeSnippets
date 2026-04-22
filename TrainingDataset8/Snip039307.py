def test_clear_single_cache(self, _, cache_decorator):
        foo_call_count = [0]

        @cache_decorator
        def foo():
            foo_call_count[0] += 1

        bar_call_count = [0]

        @cache_decorator
        def bar():
            bar_call_count[0] += 1

        foo(), foo(), foo()
        bar(), bar(), bar()
        self.assertEqual(1, foo_call_count[0])
        self.assertEqual(1, bar_call_count[0])

        # Clear just foo's cache, and call the functions again.
        foo.clear()

        foo(), foo(), foo()
        bar(), bar(), bar()

        # Foo will have been called a second time, and bar will still
        # have been called just once.
        self.assertEqual(2, foo_call_count[0])
        self.assertEqual(1, bar_call_count[0])