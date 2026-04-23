def test_just_order_with_respect_to_no_errors(self):
        class Question(models.Model):
            pass

        class Answer(models.Model):
            question = models.ForeignKey(Question, models.CASCADE)

            class Meta:
                order_with_respect_to = "question"

        self.assertEqual(Answer.check(), [])