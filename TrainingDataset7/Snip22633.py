def test_multiplechoicefield_2(self):
        f = MultipleChoiceField(choices=[("1", "One"), ("2", "Two")], required=False)
        self.assertEqual([], f.clean(""))
        self.assertEqual([], f.clean(None))
        self.assertEqual(["1"], f.clean([1]))
        self.assertEqual(["1"], f.clean(["1"]))
        self.assertEqual(["1", "2"], f.clean(["1", "2"]))
        self.assertEqual(["1", "2"], f.clean([1, "2"]))
        self.assertEqual(["1", "2"], f.clean((1, "2")))
        with self.assertRaisesMessage(ValidationError, "'Enter a list of values.'"):
            f.clean("hello")
        self.assertEqual([], f.clean([]))
        self.assertEqual([], f.clean(()))
        msg = "'Select a valid choice. 3 is not one of the available choices.'"
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean(["3"])