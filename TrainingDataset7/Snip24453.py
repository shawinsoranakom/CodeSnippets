def test07_allowed_types(self):
        "Type-restricted list"
        pl, ul = self.lists_of_len()
        ul._allowed = int
        ul[1] = 50
        ul[:2] = [60, 70, 80]

        def setfcn(x, i, v):
            x[i] = v

        msg = "Invalid type encountered in the arguments."
        with self.assertRaisesMessage(TypeError, msg):
            setfcn(ul, 2, "hello")
        with self.assertRaisesMessage(TypeError, msg):
            setfcn(ul, slice(0, 3, 2), ("hello", "goodbye"))