def test_search_two_terms(self):
        self.check_default_text_search_config()
        searched = Line.objects.filter(dialogue__search="heart bowel")
        self.assertSequenceEqual(searched, [self.verse2])