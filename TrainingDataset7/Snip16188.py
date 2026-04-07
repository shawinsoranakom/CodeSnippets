def test_missing_search_fields(self):
        class EmptySearchAdmin(QuestionAdmin):
            search_fields = []

        with model_admin(Question, EmptySearchAdmin):
            msg = "EmptySearchAdmin must have search_fields for the autocomplete_view."
            with self.assertRaisesMessage(Http404, msg):
                site.autocomplete_view(
                    self.factory.get(self.url, {"term": "", **self.opts})
                )