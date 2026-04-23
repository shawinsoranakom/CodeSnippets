def test_combine_raw_phrase(self):
        self.check_default_text_search_config()
        searched = Line.objects.filter(
            dialogue__search=(
                SearchQuery("burn:*", search_type="raw", config="simple")
                | SearchQuery("rode forth from Camelot", search_type="phrase")
            )
        )
        self.assertCountEqual(searched, [self.verse0, self.verse1, self.verse2])