def test_emptyqs(self):
        msg = "EmptyQuerySet can't be instantiated"
        with self.assertRaisesMessage(TypeError, msg):
            EmptyQuerySet()
        self.assertIsInstance(Article.objects.none(), EmptyQuerySet)
        self.assertNotIsInstance("", EmptyQuerySet)