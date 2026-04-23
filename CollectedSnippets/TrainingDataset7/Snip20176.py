def test_transform_on_field(self):
        author_name = Author._meta.get_field("name")
        author_alias = Author._meta.get_field("alias")
        with register_lookup(models.CharField, Div3Transform):
            self.assertEqual(author_alias.get_transform("div3"), Div3Transform)
            self.assertEqual(author_name.get_transform("div3"), Div3Transform)
        with register_lookup(author_alias, Div3Transform):
            self.assertEqual(author_alias.get_transform("div3"), Div3Transform)
            self.assertIsNone(author_name.get_transform("div3"))
        self.assertIsNone(author_alias.get_transform("div3"))
        self.assertIsNone(author_name.get_transform("div3"))