def test05_out_of_range_exceptions(self):
        "Out of range exceptions"

        def setfcn(x, i):
            x[i] = 20

        def getfcn(x, i):
            return x[i]

        def delfcn(x, i):
            del x[i]

        pl, ul = self.lists_of_len()
        for i in (-1 - self.limit, self.limit):
            msg = f"invalid index: {i}"
            with self.subTest(i=i):
                with self.assertRaisesMessage(IndexError, msg):
                    setfcn(ul, i)
                with self.assertRaisesMessage(IndexError, msg):
                    getfcn(ul, i)
                with self.assertRaisesMessage(IndexError, msg):
                    delfcn(ul, i)