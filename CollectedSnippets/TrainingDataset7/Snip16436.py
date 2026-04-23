def test_display_consecutive_whitespace_object_in_messages(self):
        buttons = ["_save", "_continue", "_addanother"]
        for button in buttons:
            body = {"author": self.obj.author, button: "1"}
            with self.subTest(obj=self.obj, button=button):
                response = self.client.post(
                    reverse("admin:admin_views_coverletter_add"), body, follow=True
                )
                latest_cl = CoverLetter.objects.latest("id")
                change_link = reverse(
                    "admin:admin_views_coverletter_change", args=(latest_cl.pk,)
                )
                self.assertContains(
                    response,
                    f'The cover letter “<a href="{change_link}">-</a>” '
                    "was added successfully.",
                )
                response = self.client.post(
                    reverse(
                        "admin:admin_views_coverletter_change", args=(latest_cl.pk,)
                    ),
                    {**body, "author": "             "},
                    follow=True,
                )
                self.assertContains(
                    response,
                    f'The cover letter “<a href="{change_link}">-</a>” '
                    "was changed successfully.",
                )

        new_obj = CoverLetter.objects.create(author=self.obj.author)
        response = self.client.post(
            reverse("admin:admin_views_coverletter_delete", args=(new_obj.pk,)),
            {"post": "yes"},
            follow=True,
        )
        self.assertContains(response, "The cover letter “-” was deleted successfully.")