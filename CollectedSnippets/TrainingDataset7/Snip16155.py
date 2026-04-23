def test_popup_template_response_on_change(self):
        instance = Actor.objects.create(name="David Tennant", age=45)
        response = self.client.post(
            reverse("admin:admin_views_actor_change", args=(instance.pk,))
            + "?%s=1" % IS_POPUP_VAR,
            {"name": "David Tennant", "age": "46", IS_POPUP_VAR: "1"},
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