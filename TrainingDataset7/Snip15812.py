def test_color_style(self):
        style = color.no_style()
        self.assertEqual(style.ERROR("Hello, world!"), "Hello, world!")

        style = color.make_style("nocolor")
        self.assertEqual(style.ERROR("Hello, world!"), "Hello, world!")

        style = color.make_style("dark")
        self.assertIn("Hello, world!", style.ERROR("Hello, world!"))
        self.assertNotEqual(style.ERROR("Hello, world!"), "Hello, world!")

        # Default palette has color.
        style = color.make_style("")
        self.assertIn("Hello, world!", style.ERROR("Hello, world!"))
        self.assertNotEqual(style.ERROR("Hello, world!"), "Hello, world!")