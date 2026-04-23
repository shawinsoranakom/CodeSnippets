def test_zip_tuple_reuse(self):
        ids = list(map(id, zip('abc', 'def')))
        self.assertEqual(min(ids), max(ids))
        ids = list(map(id, list(zip('abc', 'def'))))
        self.assertEqual(len(dict.fromkeys(ids)), len(ids))

        # check copy, deepcopy, pickle
        ans = [(x,y) for x, y in copy.copy(zip('abc',count()))]
        self.assertEqual(ans, [('a', 0), ('b', 1), ('c', 2)])

        ans = [(x,y) for x, y in copy.deepcopy(zip('abc',count()))]
        self.assertEqual(ans, [('a', 0), ('b', 1), ('c', 2)])

        for proto in range(pickle.HIGHEST_PROTOCOL + 1):
            ans = [(x,y) for x, y in pickle.loads(pickle.dumps(zip('abc',count()), proto))]
            self.assertEqual(ans, [('a', 0), ('b', 1), ('c', 2)])

        for proto in range(pickle.HIGHEST_PROTOCOL + 1):
            testIntermediate = zip('abc',count())
            next(testIntermediate)
            ans = [(x,y) for x, y in pickle.loads(pickle.dumps(testIntermediate, proto))]
            self.assertEqual(ans, [('b', 1), ('c', 2)])

        for proto in range(pickle.HIGHEST_PROTOCOL + 1):
            self.pickletest(proto, zip('abc', count()))