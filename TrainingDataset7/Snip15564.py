def test_inline_delete_buttons_are_not_shown(self):
        Question.objects.create(text="How will this be rendered?", poll=self.poll)
        response = self.client.get(self.change_url)
        self.assertNotContains(
            response,
            '<input type="checkbox" name="question_set-0-DELETE" '
            'id="id_question_set-0-DELETE">',
            html=True,
        )