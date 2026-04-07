def test_combine_different_configs(self):
        searched = Line.objects.filter(
            dialogue__search=(
                SearchQuery("cadeau", config="french")
                | SearchQuery("nostrils", config="english")
            )
        )
        self.assertCountEqual(searched, [self.french, self.verse2])