def test_relation_nested_lookup_error(self):
        # An invalid nested lookup on a related field raises a useful error.
        msg = (
            "Unsupported lookup 'editor__name' for ForeignKey or join on the field not "
            "permitted."
        )
        with self.assertRaisesMessage(FieldError, msg):
            Article.objects.filter(author__editor__name="James")
        msg = (
            "Unsupported lookup 'foo' for ForeignKey or join on the field not "
            "permitted."
        )
        with self.assertRaisesMessage(FieldError, msg):
            Tag.objects.filter(articles__foo="bar")