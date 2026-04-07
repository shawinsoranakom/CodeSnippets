def setUpTestData(cls):
        cls.question = Question.objects.create(text="question")
        cls.answer = Answer.objects.create(text="answer", question=cls.question)