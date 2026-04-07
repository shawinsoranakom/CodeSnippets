def test_related_field(self):
        questions_data = (
            # (posted data, number of answers),
            (datetime.date(2001, 1, 30), 0),
            (datetime.date(2003, 3, 15), 1),
            (datetime.date(2005, 5, 3), 2),
        )
        for date, answer_count in questions_data:
            question = Question.objects.create(posted=date)
            for i in range(answer_count):
                question.answer_set.create()

        response = self.client.get(reverse("admin:admin_views_answer_changelist"))
        for date, answer_count in questions_data:
            link = '?question__posted__year=%d"' % date.year
            if answer_count > 0:
                self.assertContains(response, link)
            else:
                self.assertNotContains(response, link)