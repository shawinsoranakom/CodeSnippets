def test_unsupported_lookups_custom_lookups(self):
        slug_field = Article._meta.get_field("slug")
        msg = (
            "Unsupported lookup 'lengtp' for SlugField or join on the field not "
            "permitted, perhaps you meant length?"
        )
        with self.assertRaisesMessage(FieldError, msg):
            with register_lookup(slug_field, Length):
                Article.objects.filter(slug__lengtp=20)