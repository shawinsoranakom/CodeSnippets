def test_deferred_queryset_context_object_name(self):
        class FormContext(ModelFormMixin):
            request = RequestFactory().get("/")
            model = Author
            object = Author.objects.defer("name").get(pk=self.author1.pk)
            fields = ("name",)

        form_context_data = FormContext().get_context_data()
        self.assertEqual(form_context_data["object"], self.author1)
        self.assertEqual(form_context_data["author"], self.author1)