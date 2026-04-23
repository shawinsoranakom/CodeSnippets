def test_path_with_querystring_and_fragment(self):
        relpath = self.hashed_file_path("cached/css/fragments.css")
        self.assertEqual(relpath, "cached/css/fragments.7fe344dee895.css")
        with storage.staticfiles_storage.open(relpath) as relfile:
            content = relfile.read()
            self.assertIn(b"fonts/font.b9b105392eb8.eot?#iefix", content)
            self.assertIn(b"fonts/font.b8d603e42714.svg#webfontIyfZbseF", content)
            self.assertIn(
                b"fonts/font.b8d603e42714.svg#path/to/../../fonts/font.svg", content
            )
            self.assertIn(
                b"data:font/woff;charset=utf-8;"
                b"base64,d09GRgABAAAAADJoAA0AAAAAR2QAAQAAAAAAAAAAAAA",
                content,
            )
            self.assertIn(b"#default#VML", content)
        self.assertPostCondition()