def test_change_form_URL_has_correct_value(self):
        """
        change_view has form_url in response.context
        """
        response = self.client.get(
            reverse(
                "admin:admin_views_section_change",
                args=(self.s1.pk,),
                current_app=self.current_app,
            )
        )
        self.assertIn(
            "form_url", response.context, msg="form_url not present in response.context"
        )
        self.assertEqual(response.context["form_url"], "pony")