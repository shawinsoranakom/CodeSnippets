def test_class_fixtures(self):
        "There were no fixture objects installed"
        self.assertEqual(Article.objects.count(), 0)