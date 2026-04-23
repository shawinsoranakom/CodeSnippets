def test_combined_configs(self):
        searched = Line.objects.filter(
            dialogue__search=(
                SearchQuery("nostrils", config="simple")
                & SearchQuery("bowels", config="simple")
            ),
        )
        self.assertSequenceEqual(searched, [self.verse2])