def test_add_view(self):
        """Test add view restricts access and actually adds items."""
        add_dict = {
            "title": "Døm ikke",
            "content": "<p>great article</p>",
            "date_0": "2008-03-18",
            "date_1": "10:54:39",
            "section": self.s1.pk,
        }
        # Change User should not have access to add articles
        self.client.force_login(self.changeuser)
        # make sure the view removes test cookie
        self.assertIs(self.client.session.test_cookie_worked(), False)
        response = self.client.get(reverse("admin:admin_views_article_add"))
        self.assertEqual(response.status_code, 403)
        # Try POST just to make sure
        post = self.client.post(reverse("admin:admin_views_article_add"), add_dict)
        self.assertEqual(post.status_code, 403)
        self.assertEqual(Article.objects.count(), 3)
        self.client.post(reverse("admin:logout"))

        # View User should not have access to add articles
        self.client.force_login(self.viewuser)
        response = self.client.get(reverse("admin:admin_views_article_add"))
        self.assertEqual(response.status_code, 403)
        # Try POST just to make sure
        post = self.client.post(reverse("admin:admin_views_article_add"), add_dict)
        self.assertEqual(post.status_code, 403)
        self.assertEqual(Article.objects.count(), 3)
        # Now give the user permission to add but not change.
        self.viewuser.user_permissions.add(
            get_perm(Article, get_permission_codename("add", Article._meta))
        )
        response = self.client.get(reverse("admin:admin_views_article_add"))
        self.assertEqual(response.context["title"], "Add article")
        self.assertContains(response, "<title>Add article | Django site admin</title>")
        self.assertContains(
            response, '<input type="submit" value="Save and view" name="_continue">'
        )
        self.assertContains(
            response,
            '<h2 id="fieldset-0-0-heading" class="fieldset-heading">Some fields</h2>',
        )
        self.assertContains(
            response,
            '<h2 id="fieldset-0-1-heading" class="fieldset-heading">'
            "Some other fields</h2>",
        )
        self.assertContains(
            response,
            '<h2 id="fieldset-0-2-heading" class="fieldset-heading">이름</h2>',
        )
        post = self.client.post(
            reverse("admin:admin_views_article_add"), add_dict, follow=False
        )
        self.assertEqual(post.status_code, 302)
        self.assertEqual(Article.objects.count(), 4)
        article = Article.objects.latest("pk")
        response = self.client.get(
            reverse("admin:admin_views_article_change", args=(article.pk,))
        )
        self.assertContains(
            response,
            '<li class="success">The article “Døm ikke” was added successfully.</li>',
        )
        article.delete()
        self.client.post(reverse("admin:logout"))

        # Add user may login and POST to add view, then redirect to admin root
        self.client.force_login(self.adduser)
        addpage = self.client.get(reverse("admin:admin_views_article_add"))
        change_list_link = '<a href="%s">Articles</a>' % reverse(
            "admin:admin_views_article_changelist"
        )
        self.assertNotContains(
            addpage,
            change_list_link,
            msg_prefix=(
                "User restricted to add permission is given link to change list view "
                "in breadcrumbs."
            ),
        )
        post = self.client.post(reverse("admin:admin_views_article_add"), add_dict)
        self.assertRedirects(post, self.index_url)
        self.assertEqual(Article.objects.count(), 4)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[0].subject, "Greetings from a created object")
        self.client.post(reverse("admin:logout"))

        # The addition was logged correctly
        addition_log = LogEntry.objects.all()[0]
        new_article = Article.objects.last()
        article_ct = ContentType.objects.get_for_model(Article)
        self.assertEqual(addition_log.user_id, self.adduser.pk)
        self.assertEqual(addition_log.content_type_id, article_ct.pk)
        self.assertEqual(addition_log.object_id, str(new_article.pk))
        self.assertEqual(addition_log.object_repr, "Døm ikke")
        self.assertEqual(addition_log.action_flag, ADDITION)
        self.assertEqual(addition_log.get_change_message(), "Added.")

        # Super can add too, but is redirected to the change list view
        self.client.force_login(self.superuser)
        addpage = self.client.get(reverse("admin:admin_views_article_add"))
        self.assertContains(
            addpage,
            change_list_link,
            msg_prefix=(
                "Unrestricted user is not given link to change list view in "
                "breadcrumbs."
            ),
        )
        post = self.client.post(reverse("admin:admin_views_article_add"), add_dict)
        self.assertRedirects(post, reverse("admin:admin_views_article_changelist"))
        self.assertEqual(Article.objects.count(), 5)
        self.client.post(reverse("admin:logout"))

        # 8509 - if a normal user is already logged in, it is possible
        # to change user into the superuser without error
        self.client.force_login(self.joepublicuser)
        # Check and make sure that if user expires, data still persists
        self.client.force_login(self.superuser)
        # make sure the view removes test cookie
        self.assertIs(self.client.session.test_cookie_worked(), False)