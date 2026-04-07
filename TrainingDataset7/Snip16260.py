def test_inclusion_admin_node_deferred_annotation(self):
        def action(arg: SomeType = None):  # NOQA: F821
            pass

        # This used to raise TypeError via the underlying call to
        # inspect.getfullargspec(), which is not ready for deferred
        # evaluation of annotations.
        InclusionAdminNode(
            "test",
            parser=object(),
            token=Token(token_type=TokenType.TEXT, contents="a"),
            func=action,
            template_name="test.html",
            takes_context=False,
        )