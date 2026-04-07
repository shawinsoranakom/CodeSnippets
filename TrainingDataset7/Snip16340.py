def test_date_hierarchy_local_date_differ_from_utc(self):
        # This datetime is 2017-01-01 in UTC.
        for date in make_aware_datetimes(
            datetime.datetime(2016, 12, 31, 16), "America/Los_Angeles"
        ):
            with self.subTest(repr(date.tzinfo)):
                q = Question.objects.create(question="Why?", expires=date)
                Answer2.objects.create(question=q, answer="Because.")
                response = self.client.get(
                    reverse("admin:admin_views_answer2_changelist")
                )
                self.assertContains(response, "question__expires__day=31")
                self.assertContains(response, "question__expires__month=12")
                self.assertContains(response, "question__expires__year=2016")