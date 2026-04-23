def test_popup_template_response_on_add(self):
        """
        Success on popups shall be rendered from template in order to allow
        easy customization.
        """
        response = self.client.post(
            reverse("admin:admin_views_actor_add") + "?%s=1" % IS_POPUP_VAR,
            {"name": "Troy McClure", "age": "55", IS_POPUP_VAR: "1"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.template_name,
            [
                "admin/admin_views/actor/popup_response.html",
                "admin/admin_views/popup_response.html",
                "admin/popup_response.html",
            ],
        )
        self.assertTemplateUsed(response, "admin/popup_response.html")