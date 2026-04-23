def test_hamt_stress(self):
        COLLECTION_SIZE = 7000
        TEST_ITERS_EVERY = 647
        CRASH_HASH_EVERY = 97
        CRASH_EQ_EVERY = 11
        RUN_XTIMES = 3

        for _ in range(RUN_XTIMES):
            h = hamt()
            d = dict()

            for i in range(COLLECTION_SIZE):
                key = KeyStr(i)

                if not (i % CRASH_HASH_EVERY):
                    with HaskKeyCrasher(error_on_hash=True):
                        with self.assertRaises(HashingError):
                            h.set(key, i)

                h = h.set(key, i)

                if not (i % CRASH_EQ_EVERY):
                    with HaskKeyCrasher(error_on_eq=True):
                        with self.assertRaises(EqError):
                            h.get(KeyStr(i))  # really trigger __eq__

                d[key] = i
                self.assertEqual(len(d), len(h))

                if not (i % TEST_ITERS_EVERY):
                    self.assertEqual(set(h.items()), set(d.items()))
                    self.assertEqual(len(h.items()), len(d.items()))

            self.assertEqual(len(h), COLLECTION_SIZE)

            for key in range(COLLECTION_SIZE):
                self.assertEqual(h.get(KeyStr(key), 'not found'), key)

            keys_to_delete = list(range(COLLECTION_SIZE))
            random.shuffle(keys_to_delete)
            for iter_i, i in enumerate(keys_to_delete):
                key = KeyStr(i)

                if not (iter_i % CRASH_HASH_EVERY):
                    with HaskKeyCrasher(error_on_hash=True):
                        with self.assertRaises(HashingError):
                            h.delete(key)

                if not (iter_i % CRASH_EQ_EVERY):
                    with HaskKeyCrasher(error_on_eq=True):
                        with self.assertRaises(EqError):
                            h.delete(KeyStr(i))

                h = h.delete(key)
                self.assertEqual(h.get(key, 'not found'), 'not found')
                del d[key]
                self.assertEqual(len(d), len(h))

                if iter_i == COLLECTION_SIZE // 2:
                    hm = h
                    dm = d.copy()

                if not (iter_i % TEST_ITERS_EVERY):
                    self.assertEqual(set(h.keys()), set(d.keys()))
                    self.assertEqual(len(h.keys()), len(d.keys()))

            self.assertEqual(len(d), 0)
            self.assertEqual(len(h), 0)

            # ============

            for key in dm:
                self.assertEqual(hm.get(str(key)), dm[key])
            self.assertEqual(len(dm), len(hm))

            for i, key in enumerate(keys_to_delete):
                hm = hm.delete(str(key))
                self.assertEqual(hm.get(str(key), 'not found'), 'not found')
                dm.pop(str(key), None)
                self.assertEqual(len(d), len(h))

                if not (i % TEST_ITERS_EVERY):
                    self.assertEqual(set(h.values()), set(d.values()))
                    self.assertEqual(len(h.values()), len(d.values()))

            self.assertEqual(len(d), 0)
            self.assertEqual(len(h), 0)
            self.assertEqual(list(h.items()), [])