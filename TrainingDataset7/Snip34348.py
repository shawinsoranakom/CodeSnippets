def test_tag_call(self):
        def func(parser, token):
            return Node()

        self.library.tag("name", func)
        self.assertEqual(self.library.tags["name"], func)