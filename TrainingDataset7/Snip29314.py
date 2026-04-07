def setUpTestData(cls):
        cls.q1 = cls.Question.objects.create(
            text="Which Beatle starts with the letter 'R'?"
        )
        cls.Answer.objects.create(text="John", question=cls.q1)
        cls.Answer.objects.create(text="Paul", question=cls.q1)
        cls.Answer.objects.create(text="George", question=cls.q1)
        cls.Answer.objects.create(text="Ringo", question=cls.q1)