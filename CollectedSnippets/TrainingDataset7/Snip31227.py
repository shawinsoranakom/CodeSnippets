def setUpTestData(cls):
        john = User.objects.create(name="John Doe")
        jim = User.objects.create(name="Jim Bo")
        first_poll = Poll.objects.create(
            question="What's the first question?", creator=john
        )
        second_poll = Poll.objects.create(
            question="What's the second question?", creator=jim
        )
        Choice.objects.create(
            poll=first_poll, related_poll=second_poll, name="This is the answer."
        )