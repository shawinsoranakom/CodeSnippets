def test_inlines_are_rendered_as_read_only(self):
        question = Question.objects.create(
            text="How will this be rendered?", poll=self.poll
        )
        response = self.client.get(self.change_url)
        self.assertContains(
            response, '<td class="field-text"><p>%s</p></td>' % question.text, html=True
        )
        self.assertNotContains(response, 'id="id_question_set-0-text"')
        self.assertNotContains(response, 'id="id_related_objs-0-DELETE"')