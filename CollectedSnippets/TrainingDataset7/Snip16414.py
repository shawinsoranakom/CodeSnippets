def test_delete_view(self):
        """Delete view should restrict access and actually delete items."""
        delete_dict = {"post": "yes"}
        delete_url = reverse("admin:admin_views_article_delete", args=(self.a1.pk,))

        # add user should not be able to delete articles
        self.client.force_login(self.adduser)
        response = self.client.get(delete_url)
        self.assertEqual(response.status_code, 403)
        post = self.client.post(delete_url, delete_dict)
        self.assertEqual(post.status_code, 403)
        self.assertEqual(Article.objects.count(), 3)
        self.client.logout()

        # view user should not be able to delete articles
        self.client.force_login(self.viewuser)
        response = self.client.get(delete_url)
        self.assertEqual(response.status_code, 403)
        post = self.client.post(delete_url, delete_dict)
        self.assertEqual(post.status_code, 403)
        self.assertEqual(Article.objects.count(), 3)
        self.client.logout()

        # Delete user can delete
        self.client.force_login(self.deleteuser)
        response = self.client.get(
            reverse("admin:admin_views_section_delete", args=(self.s1.pk,))
        )
        self.assertContains(response, "<h1>Delete</h1>")
        self.assertContains(response, "<h2>Summary</h2>")
        self.assertContains(response, "<li>Articles: 3</li>")
        # test response contains link to related Article
        self.assertContains(response, "admin_views/article/%s/" % self.a1.pk)

        response = self.client.get(delete_url)
        self.assertContains(response, "admin_views/article/%s/" % self.a1.pk)
        self.assertContains(response, "<h2>Summary</h2>")
        self.assertContains(response, "<li>Articles: 1</li>")
        post = self.client.post(delete_url, delete_dict)
        self.assertRedirects(post, self.index_url)
        self.assertEqual(Article.objects.count(), 2)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Greetings from a deleted object")
        article_ct = ContentType.objects.get_for_model(Article)
        logged = LogEntry.objects.get(content_type=article_ct, action_flag=DELETION)
        self.assertEqual(logged.object_id, str(self.a1.pk))