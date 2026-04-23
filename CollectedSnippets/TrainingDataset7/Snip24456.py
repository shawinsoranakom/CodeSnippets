def test10_checkindex(self):
        "Index check"
        pl, ul = self.lists_of_len()
        for i in self.limits_plus(0):
            with self.subTest(i=i):
                if i < 0:
                    self.assertEqual(
                        ul._checkindex(i), i + self.limit, "_checkindex(neg index)"
                    )
                else:
                    self.assertEqual(ul._checkindex(i), i, "_checkindex(pos index)")

        for i in (-self.limit - 1, self.limit):
            with (
                self.subTest(i=i),
                self.assertRaisesMessage(IndexError, f"invalid index: {i}"),
            ):
                ul._checkindex(i)