def test_instance_lookup_override(self):
        author_name = Author._meta.get_field("name")
        with register_lookup(author_name, CustomStartsWith, lookup_name="st_end"):
            self.assertEqual(author_name.get_lookup("st_end"), CustomStartsWith)
            author_name.register_lookup(CustomEndsWith, lookup_name="st_end")
            self.assertEqual(author_name.get_lookup("st_end"), CustomEndsWith)
        self.assertIsNone(author_name.get_lookup("st_end"))