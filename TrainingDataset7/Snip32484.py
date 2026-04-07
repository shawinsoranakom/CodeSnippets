def test_template_tag_return(self):
        self.assertStaticRaises(
            ValueError, "does/not/exist.png", "/static/does/not/exist.png"
        )
        self.assertStaticRenders("test/file.txt", "/static/test/file.dad0999e4f8f.txt")
        self.assertStaticRenders(
            "test/file.txt", "/static/test/file.dad0999e4f8f.txt", asvar=True
        )
        self.assertStaticRenders(
            "cached/styles.css", "/static/cached/styles.5e0040571e1a.css"
        )
        self.assertStaticRenders("path/", "/static/path/")
        self.assertStaticRenders("path/?query", "/static/path/?query")
        self.assertPostCondition()