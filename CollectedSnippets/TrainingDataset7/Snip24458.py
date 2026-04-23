def test_12_arithmetic(self):
        "Arithmetic"
        pl, ul = self.lists_of_len()
        al = list(range(10, 14))
        self.assertEqual(list(pl + al), list(ul + al), "add")
        self.assertEqual(type(ul), type(ul + al), "type of add result")
        self.assertEqual(list(al + pl), list(al + ul), "radd")
        self.assertEqual(type(al), type(al + ul), "type of radd result")
        objid = id(ul)
        pl += al
        ul += al
        self.assertEqual(pl[:], ul[:], "in-place add")
        self.assertEqual(objid, id(ul), "in-place add id")

        for n in (-1, 0, 1, 3):
            pl, ul = self.lists_of_len()
            self.assertEqual(list(pl * n), list(ul * n), "mul by %d" % n)
            self.assertEqual(type(ul), type(ul * n), "type of mul by %d result" % n)
            self.assertEqual(list(n * pl), list(n * ul), "rmul by %d" % n)
            self.assertEqual(type(ul), type(n * ul), "type of rmul by %d result" % n)
            objid = id(ul)
            pl *= n
            ul *= n
            self.assertEqual(pl[:], ul[:], "in-place mul by %d" % n)
            self.assertEqual(objid, id(ul), "in-place mul by %d id" % n)

        pl, ul = self.lists_of_len()
        self.assertEqual(pl, ul, "cmp for equal")
        self.assertNotEqual(ul, pl + [2], "cmp for not equal")
        self.assertGreaterEqual(pl, ul, "cmp for gte self")
        self.assertLessEqual(pl, ul, "cmp for lte self")
        self.assertGreaterEqual(ul, pl, "cmp for self gte")
        self.assertLessEqual(ul, pl, "cmp for self lte")

        self.assertGreater(pl + [5], ul, "cmp")
        self.assertGreaterEqual(pl + [5], ul, "cmp")
        self.assertLess(pl, ul + [2], "cmp")
        self.assertLessEqual(pl, ul + [2], "cmp")
        self.assertGreater(ul + [5], pl, "cmp")
        self.assertGreaterEqual(ul + [5], pl, "cmp")
        self.assertLess(ul, pl + [2], "cmp")
        self.assertLessEqual(ul, pl + [2], "cmp")

        pl[1] = 20
        self.assertGreater(pl, ul, "cmp for gt self")
        self.assertLess(ul, pl, "cmp for self lt")
        pl[1] = -20
        self.assertLess(pl, ul, "cmp for lt self")
        self.assertGreater(ul, pl, "cmp for gt self")