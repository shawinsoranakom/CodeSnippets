def assertBorder(self, element, border):
        width, style, color = border.split(" ")
        border_properties = [
            "border-bottom-%s",
            "border-left-%s",
            "border-right-%s",
            "border-top-%s",
        ]
        for prop in border_properties:
            self.assertEqual(element.value_of_css_property(prop % "width"), width)
        for prop in border_properties:
            self.assertEqual(element.value_of_css_property(prop % "style"), style)
        # Convert hex color to rgb.
        self.assertRegex(color, "#[0-9a-f]{6}")
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:], 16)
        # The value may be expressed as either rgb() or rgba() depending on the
        # browser.
        colors = [
            "rgb(%d, %d, %d)" % (r, g, b),
            "rgba(%d, %d, %d, 1)" % (r, g, b),
        ]
        for prop in border_properties:
            self.assertIn(element.value_of_css_property(prop % "color"), colors)