def test_mixed_char_text(self):
        Article.objects.create(
            title="The Title", text=lorem_ipsum, written=timezone.now()
        )
        article = Article.objects.annotate(
            title_text=Concat("title", V(" - "), "text", output_field=TextField()),
        ).get(title="The Title")
        self.assertEqual(article.title + " - " + article.text, article.title_text)
        # Wrap the concat in something else to ensure that text is returned
        # rather than bytes.
        article = Article.objects.annotate(
            title_text=Upper(
                Concat("title", V(" - "), "text", output_field=TextField())
            ),
        ).get(title="The Title")
        expected = article.title + " - " + article.text
        self.assertEqual(expected.upper(), article.title_text)