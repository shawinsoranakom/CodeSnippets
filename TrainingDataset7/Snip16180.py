def test_to_field_resolution_with_fk_pk(self):
        p = Parent.objects.create(name="Bertie")
        c = PKChild.objects.create(parent=p, name="Anna")
        opts = {
            "app_label": Toy._meta.app_label,
            "model_name": Toy._meta.model_name,
            "field_name": "child",
        }
        request = self.factory.get(self.url, {"term": "anna", **opts})
        request.user = self.superuser
        response = AutocompleteJsonView.as_view(**self.as_view_args)(request)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.text)
        self.assertEqual(
            data,
            {
                "results": [{"id": str(c.pk), "text": c.name}],
                "pagination": {"more": False},
            },
        )