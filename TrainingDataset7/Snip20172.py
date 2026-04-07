def test_instance_lookup(self):
        author_name = Author._meta.get_field("name")
        author_alias = Author._meta.get_field("alias")
        with register_lookup(author_name, CustomStartsWith):
            self.assertEqual(author_name.instance_lookups, {"sw": CustomStartsWith})
            self.assertEqual(author_name.get_lookup("sw"), CustomStartsWith)
            self.assertIsNone(author_alias.get_lookup("sw"))
        self.assertIsNone(author_name.get_lookup("sw"))
        self.assertEqual(author_name.instance_lookups, {})
        self.assertIsNone(author_alias.get_lookup("sw"))