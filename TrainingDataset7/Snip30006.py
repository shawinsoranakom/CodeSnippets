def test_non_exact_match(self):
        self.check_default_text_search_config()
        searched = Line.objects.filter(dialogue__search="hearts")
        self.assertSequenceEqual(searched, [self.verse2])