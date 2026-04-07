def test_duplicate_querysets(self):
        question = Question.objects.create(text="What is your name?")
        answer = Answer.objects.create(text="Joe", question=question)
        answer = Answer.objects.get(pk=answer.pk)
        msg = "Only one queryset is allowed for each content type."
        with self.assertRaisesMessage(ValueError, msg):
            models.prefetch_related_objects(
                [answer],
                GenericPrefetch(
                    "question",
                    [
                        Question.objects.all(),
                        Question.objects.filter(text__startswith="test"),
                    ],
                ),
            )