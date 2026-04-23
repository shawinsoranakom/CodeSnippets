def test_submit_line_shows_only_close_button(self):
        response = self.client.get(self.change_url)
        self.assertContains(
            response,
            '<a role="button" href="/admin/admin_inlines/poll/" class="closelink">'
            "Close</a>",
            html=True,
        )
        delete_link = (
            '<a role="button" href="/admin/admin_inlines/poll/%s/delete/" '
            'class="deletelink">Delete</a>'
        )
        self.assertNotContains(response, delete_link % self.poll.id, html=True)
        self.assertNotContains(
            response,
            '<input type="submit" value="Save and add another" name="_addanother">',
        )
        self.assertNotContains(
            response,
            '<input type="submit" value="Save and continue editing" name="_continue">',
        )