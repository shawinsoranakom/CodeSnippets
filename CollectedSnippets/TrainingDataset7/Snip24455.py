def test09_iterable_check(self):
        "Error on assigning non-iterable to slice"
        pl, ul = self.lists_of_len(self.limit + 1)

        def setfcn(x, i, v):
            x[i] = v

        with self.assertRaisesMessage(
            TypeError, "can only assign an iterable to a slice"
        ):
            setfcn(ul, slice(0, 3, 2), 2)