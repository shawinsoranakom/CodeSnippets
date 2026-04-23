def test_previous_and_next_in_order(self):
        # We can retrieve the answers related to a particular object, in the
        # order they were created, once we have a particular object.
        a1 = self.q1.answer_set.all()[0]
        self.assertEqual(a1.text, "John")
        self.assertEqual(a1.get_next_in_order().text, "Paul")

        a2 = list(self.q1.answer_set.all())[-1]
        self.assertEqual(a2.text, "Ringo")
        self.assertEqual(a2.get_previous_in_order().text, "George")