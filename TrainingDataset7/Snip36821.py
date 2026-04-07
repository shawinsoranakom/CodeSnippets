def test_validation_with_empty_blank_field(self):
        # Since a value for pub_date wasn't provided and the field is
        # blank=True, model-validation should pass.
        # Also, Article.clean() should be run, so pub_date will be filled after
        # validation, so the form should save cleanly even though pub_date is
        # not allowed to be null.
        data = {
            "title": "The state of model validation",
        }
        article = Article(author_id=self.author.id)
        form = ArticleForm(data, instance=article)
        self.assertEqual(list(form.errors), [])
        self.assertIsNotNone(form.instance.pub_date)
        article = form.save()