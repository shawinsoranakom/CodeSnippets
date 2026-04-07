def test_instance_lookup_override_class_lookups(self):
        author_name = Author._meta.get_field("name")
        author_alias = Author._meta.get_field("alias")
        with register_lookup(models.CharField, CustomStartsWith, lookup_name="st_end"):
            with register_lookup(author_alias, CustomEndsWith, lookup_name="st_end"):
                self.assertEqual(author_name.get_lookup("st_end"), CustomStartsWith)
                self.assertEqual(author_alias.get_lookup("st_end"), CustomEndsWith)
            self.assertEqual(author_name.get_lookup("st_end"), CustomStartsWith)
            self.assertEqual(author_alias.get_lookup("st_end"), CustomStartsWith)
        self.assertIsNone(author_name.get_lookup("st_end"))
        self.assertIsNone(author_alias.get_lookup("st_end"))