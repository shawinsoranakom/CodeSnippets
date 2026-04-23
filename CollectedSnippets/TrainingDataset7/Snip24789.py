def test_non_default_encoding(self):
        """#13572 - QueryDict with a non-default encoding"""
        q = QueryDict("cur=%A4", encoding="iso-8859-15")
        self.assertEqual(q.encoding, "iso-8859-15")
        self.assertEqual(list(q.items()), [("cur", "€")])
        self.assertEqual(q.urlencode(), "cur=%A4")
        q = q.copy()
        self.assertEqual(q.encoding, "iso-8859-15")
        self.assertEqual(list(q.items()), [("cur", "€")])
        self.assertEqual(q.urlencode(), "cur=%A4")
        self.assertEqual(copy.copy(q).encoding, "iso-8859-15")
        self.assertEqual(copy.deepcopy(q).encoding, "iso-8859-15")