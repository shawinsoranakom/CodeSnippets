def _test_readonly_foreignkey_links(self, admin_site):
        """
        ForeignKey readonly fields render as links if the target model is
        registered in admin.
        """
        chapter = Chapter.objects.create(
            title="Chapter 1",
            content="content",
            book=Book.objects.create(name="Book 1"),
        )
        language = Language.objects.create(iso="_40", name="Test")
        obj = ReadOnlyRelatedField.objects.create(
            chapter=chapter,
            language=language,
            user=self.superuser,
        )
        response = self.client.get(
            reverse(
                f"{admin_site}:admin_views_readonlyrelatedfield_change", args=(obj.pk,)
            ),
        )
        # Related ForeignKey object registered in admin.
        user_url = reverse(f"{admin_site}:auth_user_change", args=(self.superuser.pk,))
        self.assertContains(
            response,
            '<div class="readonly"><a href="%s">super</a></div>' % user_url,
            html=True,
        )
        # Related ForeignKey with the string primary key registered in admin.
        language_url = reverse(
            f"{admin_site}:admin_views_language_change",
            args=(quote(language.pk),),
        )
        self.assertContains(
            response,
            '<div class="readonly"><a href="%s">_40</a></div>' % language_url,
            html=True,
        )
        # Related ForeignKey object not registered in admin.
        self.assertContains(
            response, '<div class="readonly">Chapter 1</div>', html=True
        )