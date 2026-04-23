def test08_min_length(self):
        "Length limits"
        pl, ul = self.lists_of_len(5)
        ul._minlength = 3

        def delfcn(x, i):
            del x[:i]

        def setfcn(x, i):
            x[:i] = []

        msg = "Must have at least 3 items"
        for i in range(len(ul) - ul._minlength + 1, len(ul)):
            with self.subTest(i=i):
                with self.assertRaisesMessage(ValueError, msg):
                    delfcn(ul, i)
                with self.assertRaisesMessage(ValueError, msg):
                    setfcn(ul, i)
        del ul[: len(ul) - ul._minlength]

        ul._maxlength = 4
        for i in range(0, ul._maxlength - len(ul)):
            with self.subTest(i=i):
                ul.append(i)
        with self.assertRaisesMessage(ValueError, "Cannot have more than 4 items"):
            ul.append(10)