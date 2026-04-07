def test04_get_set_del_single(self):
        "Get/set/delete single item"
        pl, ul = self.lists_of_len()
        for i in self.limits_plus(0):
            with self.subTest(i=i):
                self.assertEqual(pl[i], ul[i], "get single item [%d]" % i)

        for i in self.limits_plus(0):
            pl, ul = self.lists_of_len()
            pl[i] = 100
            ul[i] = 100
            with self.subTest(i=i):
                self.assertEqual(pl[:], ul[:], "set single item [%d]" % i)

        for i in self.limits_plus(0):
            pl, ul = self.lists_of_len()
            del pl[i]
            del ul[i]
            with self.subTest(i=i):
                self.assertEqual(pl[:], ul[:], "del single item [%d]" % i)