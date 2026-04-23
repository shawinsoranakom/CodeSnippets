def test_deconstruct_nested(self):
        q = Q(Q(price__gt=F("discounted_price")))
        path, args, kwargs = q.deconstruct()
        self.assertEqual(args, (Q(price__gt=F("discounted_price")),))
        self.assertEqual(kwargs, {})