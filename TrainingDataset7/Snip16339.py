def test_date_hierarchy_timezone_dst(self):
        # This datetime doesn't exist in this timezone due to DST.
        for date in make_aware_datetimes(
            datetime.datetime(2016, 10, 16, 15), "America/Sao_Paulo"
        ):
            with self.subTest(repr(date.tzinfo)):
                q = Question.objects.create(question="Why?", expires=date)
                Answer2.objects.create(question=q, answer="Because.")
                response = self.client.get(
                    reverse("admin:admin_views_answer2_changelist")
                )
                self.assertContains(response, "question__expires__day=16")
                self.assertContains(response, "question__expires__month=10")
                self.assertContains(response, "question__expires__year=2016")