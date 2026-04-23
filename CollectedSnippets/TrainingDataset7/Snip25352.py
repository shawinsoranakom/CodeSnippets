def test_ordering_with_order_with_respect_to(self):
        class Question(models.Model):
            pass

        class Answer(models.Model):
            question = models.ForeignKey(Question, models.CASCADE)
            order = models.IntegerField()

            class Meta:
                order_with_respect_to = "question"
                ordering = ["order"]

        self.assertEqual(
            Answer.check(),
            [
                Error(
                    "'ordering' and 'order_with_respect_to' cannot be used together.",
                    obj=Answer,
                    id="models.E021",
                ),
            ],
        )