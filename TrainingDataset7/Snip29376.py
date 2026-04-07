def test_relation_traversal(self):
        self.assertIs(Article.objects.order_by("author__pk").totally_ordered, False)