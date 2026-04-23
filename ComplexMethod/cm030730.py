def test_iterator_pickle(self):
        orig = deque(range(200))
        data = [i*1.01 for i in orig]
        for proto in range(pickle.HIGHEST_PROTOCOL + 1):
            # initial iterator
            itorg = iter(orig)
            dump = pickle.dumps((itorg, orig), proto)
            it, d = pickle.loads(dump)
            for i, x in enumerate(data):
                d[i] = x
            self.assertEqual(type(it), type(itorg))
            self.assertEqual(list(it), data)

            # running iterator
            next(itorg)
            dump = pickle.dumps((itorg, orig), proto)
            it, d = pickle.loads(dump)
            for i, x in enumerate(data):
                d[i] = x
            self.assertEqual(type(it), type(itorg))
            self.assertEqual(list(it), data[1:])

            # empty iterator
            for i in range(1, len(data)):
                next(itorg)
            dump = pickle.dumps((itorg, orig), proto)
            it, d = pickle.loads(dump)
            for i, x in enumerate(data):
                d[i] = x
            self.assertEqual(type(it), type(itorg))
            self.assertEqual(list(it), [])

            # exhausted iterator
            self.assertRaises(StopIteration, next, itorg)
            dump = pickle.dumps((itorg, orig), proto)
            it, d = pickle.loads(dump)
            for i, x in enumerate(data):
                d[i] = x
            self.assertEqual(type(it), type(itorg))
            self.assertEqual(list(it), [])