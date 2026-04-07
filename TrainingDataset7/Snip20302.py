def test_dates_fails_when_no_arguments_are_provided(self):
        with self.assertRaises(TypeError):
            Article.objects.dates()