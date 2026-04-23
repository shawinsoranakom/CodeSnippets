def test06_list_methods(self):
        "List methods"
        pl, ul = self.lists_of_len()
        pl.append(40)
        ul.append(40)
        self.assertEqual(pl[:], ul[:], "append")

        pl.extend(range(50, 55))
        ul.extend(range(50, 55))
        self.assertEqual(pl[:], ul[:], "extend")

        pl.reverse()
        ul.reverse()
        self.assertEqual(pl[:], ul[:], "reverse")

        for i in self.limits_plus(1):
            pl, ul = self.lists_of_len()
            pl.insert(i, 50)
            ul.insert(i, 50)
            with self.subTest(i=i):
                self.assertEqual(pl[:], ul[:], "insert at %d" % i)

        for i in self.limits_plus(0):
            pl, ul = self.lists_of_len()
            with self.subTest(i=i):
                self.assertEqual(pl.pop(i), ul.pop(i), "popped value at %d" % i)
                self.assertEqual(pl[:], ul[:], "after pop at %d" % i)

        pl, ul = self.lists_of_len()
        self.assertEqual(pl.pop(), ul.pop(i), "popped value")
        self.assertEqual(pl[:], ul[:], "after pop")

        pl, ul = self.lists_of_len()

        def popfcn(x, i):
            x.pop(i)

        with self.assertRaisesMessage(IndexError, "invalid index: 3"):
            popfcn(ul, self.limit)
        with self.assertRaisesMessage(IndexError, "invalid index: -4"):
            popfcn(ul, -1 - self.limit)

        pl, ul = self.lists_of_len()
        for val in range(self.limit):
            with self.subTest(val=val):
                self.assertEqual(pl.index(val), ul.index(val), "index of %d" % val)

        for val in self.limits_plus(2):
            with self.subTest(val=val):
                self.assertEqual(pl.count(val), ul.count(val), "count %d" % val)

        for val in range(self.limit):
            pl, ul = self.lists_of_len()
            pl.remove(val)
            ul.remove(val)
            with self.subTest(val=val):
                self.assertEqual(pl[:], ul[:], "after remove val %d" % val)

        def indexfcn(x, v):
            return x.index(v)

        def removefcn(x, v):
            return x.remove(v)

        msg = "40 not found in object"
        with self.assertRaisesMessage(ValueError, msg):
            indexfcn(ul, 40)
        with self.assertRaisesMessage(ValueError, msg):
            removefcn(ul, 40)