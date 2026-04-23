def test_generic_relation_invalid_length(self):
        Question.objects.create(text="test")
        questions = Question.objects.all()
        msg = (
            "querysets argument of get_prefetch_querysets() should have a length of 1."
        )
        with self.assertRaisesMessage(ValueError, msg):
            questions[0].answer_set.get_prefetch_querysets(
                instances=questions,
                querysets=[Answer.objects.all(), Question.objects.all()],
            )