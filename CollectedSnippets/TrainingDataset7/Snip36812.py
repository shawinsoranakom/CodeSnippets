def test_FK_validates_using_base_manager(self):
        # Archived articles are not available through the default manager, only
        # the base manager.
        author = Author.objects.create(name="Randy", archived=True)
        article = Article(title="My Article", author=author)
        self.assertIsNone(article.full_clean())