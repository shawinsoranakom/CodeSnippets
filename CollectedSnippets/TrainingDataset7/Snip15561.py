def test_main_model_is_rendered_as_read_only(self):
        response = self.client.get(self.change_url)
        self.assertContains(
            response, '<div class="readonly">%s</div>' % self.poll.name, html=True
        )
        input = (
            '<input type="text" name="name" value="%s" class="vTextField" '
            'maxlength="40" required id="id_name">'
        )
        self.assertNotContains(response, input % self.poll.name, html=True)