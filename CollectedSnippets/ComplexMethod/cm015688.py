def test_tee_recipe(self):

        # Begin tee() recipe ###########################################

        def tee(iterable, n=2):
            if n < 0:
                raise ValueError
            if n == 0:
                return ()
            iterator = _tee(iterable)
            result = [iterator]
            for _ in range(n - 1):
                result.append(_tee(iterator))
            return tuple(result)

        class _tee:

            def __init__(self, iterable):
                it = iter(iterable)
                if isinstance(it, _tee):
                    self.iterator = it.iterator
                    self.link = it.link
                else:
                    self.iterator = it
                    self.link = [None, None]

            def __iter__(self):
                return self

            def __next__(self):
                link = self.link
                if link[1] is None:
                    link[0] = next(self.iterator)
                    link[1] = [None, None]
                value, self.link = link
                return value

        # End tee() recipe #############################################

        n = 200

        a, b = tee([])        # test empty iterator
        self.assertEqual(list(a), [])
        self.assertEqual(list(b), [])

        a, b = tee(irange(n)) # test 100% interleaved
        self.assertEqual(lzip(a,b), lzip(range(n), range(n)))

        a, b = tee(irange(n)) # test 0% interleaved
        self.assertEqual(list(a), list(range(n)))
        self.assertEqual(list(b), list(range(n)))

        a, b = tee(irange(n)) # test dealloc of leading iterator
        for i in range(100):
            self.assertEqual(next(a), i)
        del a
        self.assertEqual(list(b), list(range(n)))

        a, b = tee(irange(n)) # test dealloc of trailing iterator
        for i in range(100):
            self.assertEqual(next(a), i)
        del b
        self.assertEqual(list(a), list(range(100, n)))

        for j in range(5):   # test randomly interleaved
            order = [0]*n + [1]*n
            random.shuffle(order)
            lists = ([], [])
            its = tee(irange(n))
            for i in order:
                value = next(its[i])
                lists[i].append(value)
            self.assertEqual(lists[0], list(range(n)))
            self.assertEqual(lists[1], list(range(n)))

        # test argument format checking
        self.assertRaises(TypeError, tee)
        self.assertRaises(TypeError, tee, 3)
        self.assertRaises(TypeError, tee, [1,2], 'x')
        self.assertRaises(TypeError, tee, [1,2], 3, 'x')

        # tee object should be instantiable
        a, b = tee('abc')
        c = type(a)('def')
        self.assertEqual(list(c), list('def'))

        # test long-lagged and multi-way split
        a, b, c = tee(range(2000), 3)
        for i in range(100):
            self.assertEqual(next(a), i)
        self.assertEqual(list(b), list(range(2000)))
        self.assertEqual([next(c), next(c)], list(range(2)))
        self.assertEqual(list(a), list(range(100,2000)))
        self.assertEqual(list(c), list(range(2,2000)))

        # test invalid values of n
        self.assertRaises(TypeError, tee, 'abc', 'invalid')
        self.assertRaises(ValueError, tee, [], -1)

        for n in range(5):
            result = tee('abc', n)
            self.assertEqual(type(result), tuple)
            self.assertEqual(len(result), n)
            self.assertEqual([list(x) for x in result], [list('abc')]*n)

        # tee objects are independent (see bug gh-123884)
        a, b = tee('abc')
        c, d = tee(a)
        e, f = tee(c)
        self.assertTrue(len({a, b, c, d, e, f}) == 6)

        # test tee_new
        t1, t2 = tee('abc')
        tnew = type(t1)
        self.assertRaises(TypeError, tnew)
        self.assertRaises(TypeError, tnew, 10)
        t3 = tnew(t1)
        self.assertTrue(list(t1) == list(t2) == list(t3) == list('abc'))

        # test that tee objects are weak referenceable
        a, b = tee(range(10))
        p = weakref.proxy(a)
        self.assertEqual(getattr(p, '__class__'), type(b))
        del a
        gc.collect()  # For PyPy or other GCs.
        self.assertRaises(ReferenceError, getattr, p, '__class__')

        ans = list('abc')
        long_ans = list(range(10000))

        # Tests not applicable to the tee() recipe
        if False:
            # check copy
            a, b = tee('abc')
            self.assertEqual(list(copy.copy(a)), ans)
            self.assertEqual(list(copy.copy(b)), ans)
            a, b = tee(list(range(10000)))
            self.assertEqual(list(copy.copy(a)), long_ans)
            self.assertEqual(list(copy.copy(b)), long_ans)

            # check partially consumed copy
            a, b = tee('abc')
            take(2, a)
            take(1, b)
            self.assertEqual(list(copy.copy(a)), ans[2:])
            self.assertEqual(list(copy.copy(b)), ans[1:])
            self.assertEqual(list(a), ans[2:])
            self.assertEqual(list(b), ans[1:])
            a, b = tee(range(10000))
            take(100, a)
            take(60, b)
            self.assertEqual(list(copy.copy(a)), long_ans[100:])
            self.assertEqual(list(copy.copy(b)), long_ans[60:])
            self.assertEqual(list(a), long_ans[100:])
            self.assertEqual(list(b), long_ans[60:])

        # Issue 13454: Crash when deleting backward iterator from tee()
        forward, backward = tee(repeat(None, 2000)) # 20000000
        try:
            any(forward)  # exhaust the iterator
            del backward
        except:
            del forward, backward
            raise