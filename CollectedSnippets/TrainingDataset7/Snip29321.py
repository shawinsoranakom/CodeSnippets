def test_delete_and_insert(self):
        q1 = self.Question.objects.create(text="What is your favorite color?")
        q2 = self.Question.objects.create(text="What color is it?")
        a1 = self.Answer.objects.create(text="Blue", question=q1)
        a2 = self.Answer.objects.create(text="Red", question=q1)
        a3 = self.Answer.objects.create(text="Green", question=q1)
        a4 = self.Answer.objects.create(text="Yellow", question=q1)
        self.assertSequenceEqual(q1.answer_set.all(), [a1, a2, a3, a4])
        a3.question = q2
        a3.save()
        a1.delete()
        new_answer = self.Answer.objects.create(text="Black", question=q1)
        self.assertSequenceEqual(q1.answer_set.all(), [a2, a4, new_answer])