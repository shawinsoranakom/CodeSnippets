def test_readonly_fields(self):
        """
        File widgets should render as a link when they're marked "read only."
        """
        self.client.force_login(self.superuser)
        response = self.client.get(
            reverse("admin:admin_widgets_album_change", args=(self.album.id,))
        )
        self.assertContains(
            response,
            '<div class="readonly"><a href="%(STORAGE_URL)salbums/hybrid_theory.jpg">'
            r"albums\hybrid_theory.jpg</a></div>"
            % {"STORAGE_URL": default_storage.url("")},
            html=True,
        )
        self.assertNotContains(
            response,
            '<input type="file" name="cover_art" id="id_cover_art">',
            html=True,
        )
        response = self.client.get(reverse("admin:admin_widgets_album_add"))
        self.assertContains(
            response,
            '<div class="readonly">-</div>',
            html=True,
        )