def test_deconstruct_xor(self):
        q1 = Q(price__gt=F("discounted_price"))
        q2 = Q(price=F("discounted_price"))
        q = q1 ^ q2
        path, args, kwargs = q.deconstruct()
        self.assertEqual(
            args,
            (
                ("price__gt", F("discounted_price")),
                ("price", F("discounted_price")),
            ),
        )
        self.assertEqual(kwargs, {"_connector": Q.XOR})