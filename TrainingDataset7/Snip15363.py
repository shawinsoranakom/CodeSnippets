def test_model_with_many_to_one(self):
        link = '<a class="reference external" href="/admindocs/models/%s/">%s</a>'
        response = self.client.get(
            reverse("django-admindocs-models-detail", args=["admin_docs", "company"])
        )
        self.assertContains(
            response,
            "number of related %s objects"
            % (link % ("admin_docs.person", "admin_docs.Person")),
        )
        self.assertContains(
            response,
            "all related %s objects"
            % (link % ("admin_docs.person", "admin_docs.Person")),
        )