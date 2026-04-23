def test_value_to_string(self):
        question = Question.objects.create(text="test")
        answer1 = Answer.objects.create(question=question)
        answer2 = Answer.objects.create(question=question)
        result = json.loads(Question.answer_set.field.value_to_string(question))
        self.assertCountEqual(result, [answer1.pk, answer2.pk])