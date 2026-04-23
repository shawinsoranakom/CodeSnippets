def test_readonly_get(self):
        response = self.client.get(reverse("admin:admin_views_post_add"))
        self.assertNotContains(response, 'name="posted"')
        # 3 fields + 2 submit buttons + 5 inline management form fields, + 2
        # hidden fields for inlines + 1 field for the inline + 2 empty form
        # + 1 logout form.
        self.assertContains(response, "<input", count=17)
        self.assertContains(response, formats.localize(datetime.date.today()))
        self.assertContains(response, "<label>Awesomeness level:</label>")
        self.assertContains(response, "Very awesome.")
        self.assertContains(response, "Unknown coolness.")
        self.assertContains(response, "foo")

        # Multiline text in a readonly field gets <br> tags
        self.assertContains(response, "Multiline<br>test<br>string")
        self.assertContains(
            response,
            '<div class="readonly">Multiline<br>html<br>content</div>',
            html=True,
        )
        self.assertContains(response, "InlineMultiline<br>test<br>string")

        self.assertContains(
            response,
            formats.localize(datetime.date.today() - datetime.timedelta(days=7)),
        )

        self.assertContains(response, '<div class="form-row field-coolness">')
        self.assertContains(response, '<div class="form-row field-awesomeness_level">')
        self.assertContains(response, '<div class="form-row field-posted">')
        self.assertContains(response, '<div class="form-row field-value">')
        self.assertContains(response, '<div class="form-row">')
        self.assertContains(response, '<div class="help"', 3)
        self.assertContains(
            response,
            '<div class="help" id="id_title_helptext"><div>Some help text for the '
            "title (with Unicode ŠĐĆŽćžšđ)</div></div>",
            html=True,
        )
        self.assertContains(
            response,
            '<div class="help" id="id_content_helptext"><div>Some help text for the '
            "content (with Unicode ŠĐĆŽćžšđ)</div></div>",
            html=True,
        )
        self.assertContains(
            response,
            '<div class="help"><div>Some help text for the date (with Unicode ŠĐĆŽćžšđ)'
            "</div></div>",
            html=True,
        )

        p = Post.objects.create(
            title="I worked on readonly_fields", content="Its good stuff"
        )
        response = self.client.get(
            reverse("admin:admin_views_post_change", args=(p.pk,))
        )
        self.assertContains(response, "%s amount of cool" % p.pk)