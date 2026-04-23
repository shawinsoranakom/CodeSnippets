def test_tag_name_kwarg(self):
        @self.library.tag(name="name")
        def func(parser, token):
            return Node()

        self.assertEqual(self.library.tags["name"], func)