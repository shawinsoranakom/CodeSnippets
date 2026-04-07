def test_validation_with_invalid_blank_field(self):
        # Even though pub_date is set to blank=True, an invalid value was
        # provided, so it should fail validation.
        data = {"title": "The state of model validation", "pub_date": "never"}
        article = Article(author_id=self.author.id)
        form = ArticleForm(data, instance=article)
        self.assertEqual(list(form.errors), ["pub_date"])