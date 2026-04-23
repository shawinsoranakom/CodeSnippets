def test_tag_name_arg(self):
        @self.library.tag("name")
        def func(parser, token):
            return Node()

        self.assertEqual(self.library.tags["name"], func)