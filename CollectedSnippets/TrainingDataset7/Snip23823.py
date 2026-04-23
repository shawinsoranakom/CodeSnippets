def test_delete_with_form_as_post_with_validation_error(self):
        res = self.client.get("/edit/author/%s/delete/form/" % self.author.pk)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context["object"], self.author)
        self.assertEqual(res.context["author"], self.author)
        self.assertTemplateUsed(res, "generic_views/author_confirm_delete.html")

        res = self.client.post("/edit/author/%s/delete/form/" % self.author.pk)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.context_data["form"].errors), 2)
        self.assertEqual(
            res.context_data["form"].errors["__all__"],
            ["You must confirm the delete."],
        )
        self.assertEqual(
            res.context_data["form"].errors["confirm"],
            ["This field is required."],
        )