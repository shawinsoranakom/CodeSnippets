def test_deferred_queryset_template_name(self):
        class FormContext(SingleObjectTemplateResponseMixin):
            request = RequestFactory().get("/")
            model = Author
            object = Author.objects.defer("name").get(pk=self.author1.pk)

        self.assertEqual(
            FormContext().get_template_names()[0], "generic_views/author_detail.html"
        )