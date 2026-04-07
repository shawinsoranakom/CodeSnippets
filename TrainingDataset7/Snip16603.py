def test_readonly_text_field(self):
        p = Post.objects.create(
            title="Readonly test",
            content="test",
            readonly_content="test\r\n\r\ntest\r\n\r\ntest\r\n\r\ntest",
        )
        Link.objects.create(
            url="http://www.djangoproject.com",
            post=p,
            readonly_link_content="test\r\nlink",
        )
        response = self.client.get(
            reverse("admin:admin_views_post_change", args=(p.pk,))
        )
        # Checking readonly field.
        self.assertContains(response, "test<br><br>test<br><br>test<br><br>test")
        # Checking readonly field in inline.
        self.assertContains(response, "test<br>link")