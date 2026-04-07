def test_parallel_iterators(self):
        # Parallel iterators work.
        qs = Tag.objects.all()
        i1, i2 = iter(qs), iter(qs)
        self.assertEqual(repr(next(i1)), "<Tag: t1>")
        self.assertEqual(repr(next(i1)), "<Tag: t2>")
        self.assertEqual(repr(next(i2)), "<Tag: t1>")
        self.assertEqual(repr(next(i2)), "<Tag: t2>")
        self.assertEqual(repr(next(i2)), "<Tag: t3>")
        self.assertEqual(repr(next(i1)), "<Tag: t3>")

        qs = X.objects.all()
        self.assertFalse(qs)
        self.assertFalse(qs)