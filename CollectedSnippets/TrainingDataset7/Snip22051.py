def test_bug_19457(self):
        """
        Regression test for #19457
        get_image_dimensions() fails on some PNGs, while Image.size is working
        good on them.
        """
        img_path = os.path.join(os.path.dirname(__file__), "magic.png")
        size = images.get_image_dimensions(img_path)
        with open(img_path, "rb") as fh:
            self.assertEqual(size, Image.open(fh).size)