def test_display_consecutive_whitespace_object_in_delete_confirmation_page(self):
        response = self.client.get(
            reverse("admin:admin_views_coverletter_delete", args=(self.obj.pk,))
        )
        self.assertContains(
            response,
            "Are you sure you want to delete the cover letter “-”?",
        )

        # delete protected case
        q = Question.objects.create(question="    ")
        Answer.objects.create(question=q, answer="Because.")
        response = self.client.get(
            reverse("admin:admin_views_question_delete", args=(q.pk,))
        )
        self.assertContains(
            response,
            "Deleting the question “-” would require deleting the following protected "
            "related objects",
        )

        # delete forbidden case
        no_perms_user = User.objects.create_user(
            username="no-perm", password="secret", is_staff=True
        )
        no_perms_user.user_permissions.add(
            get_perm(Question, get_permission_codename("view", Question._meta))
        )
        no_perms_user.user_permissions.add(
            get_perm(Question, get_permission_codename("delete", Question._meta))
        )
        self.client.force_login(no_perms_user)
        response = self.client.get(
            reverse("admin:admin_views_question_delete", args=(q.pk,))
        )
        self.assertContains(
            response,
            "Deleting the question “-” would result in deleting related objects, "
            "but your account doesn't have permission to delete "
            "the following types of objects",
        )