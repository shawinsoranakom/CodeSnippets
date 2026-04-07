def test_merge_js_three_way(self):
        """
        The relative order of scripts is preserved in a three-way merge.
        """
        widget1 = Media(js=["color-picker.js"])
        widget2 = Media(js=["text-editor.js"])
        widget3 = Media(
            js=["text-editor.js", "text-editor-extras.js", "color-picker.js"]
        )
        merged = widget1 + widget2 + widget3
        self.assertEqual(
            merged._js, ["text-editor.js", "text-editor-extras.js", "color-picker.js"]
        )