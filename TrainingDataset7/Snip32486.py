def test_path_ignored_completely(self):
        relpath = self.hashed_file_path("cached/css/ignored.css")
        self.assertEqual(relpath, "cached/css/ignored.0e15ac4a4fb4.css")
        with storage.staticfiles_storage.open(relpath) as relfile:
            content = relfile.read()
            self.assertIn(b"#foobar", content)
            self.assertIn(b"http:foobar", content)
            self.assertIn(b"https:foobar", content)
            self.assertIn(b"data:foobar", content)
            self.assertIn(b"chrome:foobar", content)
            self.assertIn(b"//foobar", content)
            self.assertIn(b"url()", content)
            self.assertIn(b'/* @import url("non_exist.css") */', content)
            self.assertIn(b'/* url("non_exist.png") */', content)
            self.assertIn(b'@import url("non_exist.css")', content)
            self.assertIn(b'url("non_exist.png")', content)
            self.assertIn(b"@import url(other.css)", content)
            self.assertIn(
                b'background: #d3d6d8 /*url("does.not.exist.png")*/ '
                b'url("/static/cached/img/relative.acae32e4532b.png");',
                content,
            )
            self.assertIn(
                b'background: #d3d6d8 /* url("does.not.exist.png") */ '
                b'url("/static/cached/img/relative.acae32e4532b.png") '
                b'/*url("does.not.exist.either.png")*/',
                content,
            )
        self.assertPostCondition()