def test_filtered_many_to_many(self):
        self.assertFormfield(
            Band, "members", widgets.FilteredSelectMultiple, filter_vertical=["members"]
        )