def test_unsaved(self):
        poll = Poll(question="How?")
        msg = (
            "'Poll' instance needs to have a primary key value before this "
            "relationship can be used."
        )
        with self.assertRaisesMessage(ValueError, msg):
            poll.choice_set.all()