def test_merge_js_three_way2(self):
        # The merge prefers to place 'c' before 'b' and 'g' before 'h' to
        # preserve the original order. The preference 'c'->'b' is overridden by
        # widget3's media, but 'g'->'h' survives in the final ordering.
        widget1 = Media(js=["a", "c", "f", "g", "k"])
        widget2 = Media(js=["a", "b", "f", "h", "k"])
        widget3 = Media(js=["b", "c", "f", "k"])
        merged = widget1 + widget2 + widget3
        self.assertEqual(merged._js, ["a", "b", "c", "f", "g", "h", "k"])