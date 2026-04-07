def test_correct_autoescaping(self):
        """
        Make sure that non-field readonly elements are properly autoescaped
        (#24461)
        """
        section = Section.objects.create(name="<a>evil</a>")
        response = self.client.get(
            reverse("admin:admin_views_section_change", args=(section.pk,))
        )
        self.assertNotContains(response, "<a>evil</a>", status_code=200)
        self.assertContains(response, "&lt;a&gt;evil&lt;/a&gt;", status_code=200)