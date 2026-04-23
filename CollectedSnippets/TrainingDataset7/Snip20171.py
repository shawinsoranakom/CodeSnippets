def test_class_lookup(self):
        author_name = Author._meta.get_field("name")
        with register_lookup(models.CharField, CustomStartsWith):
            self.assertEqual(author_name.get_lookup("sw"), CustomStartsWith)
        self.assertIsNone(author_name.get_lookup("sw"))