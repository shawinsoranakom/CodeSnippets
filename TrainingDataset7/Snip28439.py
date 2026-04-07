def test_choices_type(self):
        # Choices on CharField and IntegerField
        f = ArticleForm()
        with self.assertRaises(ValidationError):
            f.fields["status"].clean("42")

        f = ArticleStatusForm()
        with self.assertRaises(ValidationError):
            f.fields["status"].clean("z")