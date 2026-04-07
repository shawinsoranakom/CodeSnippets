def test_custom_form_tabular_inline_label(self):
        """
        A model form with a form field specified (TitleForm.title1) should have
        its label rendered in the tabular inline.
        """
        response = self.client.get(reverse("admin:admin_inlines_titlecollection_add"))
        self.assertContains(
            response, '<th class="column-title1 required">Title1</th>', html=True
        )