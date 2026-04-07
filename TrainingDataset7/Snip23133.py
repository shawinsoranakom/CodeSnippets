def test_merge_css_three_way(self):
        widget1 = Media(css={"screen": ["c.css"], "all": ["d.css", "e.css"]})
        widget2 = Media(css={"screen": ["a.css"]})
        widget3 = Media(css={"screen": ["a.css", "b.css", "c.css"], "all": ["e.css"]})
        widget4 = Media(css={"all": ["d.css", "e.css"], "screen": ["c.css"]})
        merged = widget1 + widget2
        # c.css comes before a.css because widget1 + widget2 establishes this
        # order.
        self.assertEqual(
            merged._css, {"screen": ["c.css", "a.css"], "all": ["d.css", "e.css"]}
        )
        merged += widget3
        # widget3 contains an explicit ordering of c.css and a.css.
        self.assertEqual(
            merged._css,
            {"screen": ["a.css", "b.css", "c.css"], "all": ["d.css", "e.css"]},
        )
        # Media ordering does not matter.
        merged = widget1 + widget4
        self.assertEqual(merged._css, {"screen": ["c.css"], "all": ["d.css", "e.css"]})