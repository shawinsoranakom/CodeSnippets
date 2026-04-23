def test_default_ordering_override_unknown_field(self):
        """
        Attempts to override default ordering on related models with an unknown
        field should result in an error.
        """
        msg = (
            "Cannot resolve keyword 'unknown_field' into field. Choices are: "
            "article, author, editor, editor_id, id, name"
        )
        with self.assertRaisesMessage(FieldError, msg):
            list(Article.objects.order_by("author__unknown_field"))