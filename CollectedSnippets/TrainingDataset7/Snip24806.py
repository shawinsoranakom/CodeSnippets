def test_iterator_isnt_rewound(self):
        # Regression test for #13222
        r = HttpResponse("abc")
        i = iter(r)
        self.assertEqual(list(i), [b"abc"])
        self.assertEqual(list(i), [])