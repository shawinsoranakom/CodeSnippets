def test_template_detail(self):
        response = self.client.get(
            reverse(
                "django-admindocs-templates", args=["admin_doc/template_detail.html"]
            )
        )
        self.assertContains(
            response,
            "<h1>Template: <q>admin_doc/template_detail.html</q></h1>",
            html=True,
        )