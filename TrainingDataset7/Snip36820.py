def test_partial_validation(self):
        # Make sure the "commit=False and set field values later" idiom still
        # works with model validation.
        data = {
            "title": "The state of model validation",
            "pub_date": "2010-1-10 14:49:00",
        }
        form = ArticleForm(data)
        self.assertEqual(list(form.errors), [])
        article = form.save(commit=False)
        article.author = self.author
        article.save()