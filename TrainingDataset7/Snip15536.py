def test_immutable_content_type(self):
        """Regression for #9362
        The problem depends only on InlineAdminForm and its "original"
        argument, so we can safely set the other arguments to None/{}. We just
        need to check that the content_type argument of Child isn't altered by
        the internals of the inline form."""

        sally = Teacher.objects.create(name="Sally")
        john = Parent.objects.create(name="John")
        joe = Child.objects.create(name="Joe", teacher=sally, parent=john)

        iaf = InlineAdminForm(None, None, {}, {}, joe)
        parent_ct = ContentType.objects.get_for_model(Parent)
        self.assertEqual(iaf.original.content_type, parent_ct)