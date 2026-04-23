def test_model_with_no_backward_relations_render_only_relevant_fields(self):
        """
        A model with ``related_name`` of `+` shouldn't show backward
        relationship links.
        """
        response = self.client.get(
            reverse("django-admindocs-models-detail", args=["admin_docs", "family"])
        )
        fields = response.context_data.get("fields")
        self.assertEqual(len(fields), 2)