def test_template_tag(self):
        self.assertStaticRenders("does/not/exist.png", "/static/does/not/exist.png")
        self.assertStaticRenders("testfile.txt", "/static/testfile.txt")
        self.assertStaticRenders(
            "special?chars&quoted.html", "/static/special%3Fchars%26quoted.html"
        )