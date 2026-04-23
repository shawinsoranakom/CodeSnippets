def test_template_tag_return(self):
        self.assertStaticRaises(
            ValueError, "does/not/exist.png", "/static/does/not/exist.png"
        )
        self.assertStaticRenders("test/file.txt", "/static/test/file.deploy12345.txt")
        self.assertStaticRenders(
            "cached/styles.css", "/static/cached/styles.deploy12345.css"
        )
        self.assertStaticRenders("path/", "/static/path/")
        self.assertStaticRenders("path/?query", "/static/path/?query")