def test_eq(self):
        self.assertEqual(Article(id=1), Article(id=1))
        self.assertNotEqual(Article(id=1), object())
        self.assertNotEqual(object(), Article(id=1))
        a = Article()
        self.assertEqual(a, a)
        self.assertEqual(a, mock.ANY)
        self.assertNotEqual(Article(), a)