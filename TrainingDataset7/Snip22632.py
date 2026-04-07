def test_multiplechoicefield_1(self):
        f = MultipleChoiceField(choices=[("1", "One"), ("2", "Two")])
        with self.assertRaisesMessage(ValidationError, "'This field is required.'"):
            f.clean("")
        with self.assertRaisesMessage(ValidationError, "'This field is required.'"):
            f.clean(None)
        self.assertEqual(["1"], f.clean([1]))
        self.assertEqual(["1"], f.clean(["1"]))
        self.assertEqual(["1", "2"], f.clean(["1", "2"]))
        self.assertEqual(["1", "2"], f.clean([1, "2"]))
        self.assertEqual(["1", "2"], f.clean((1, "2")))
        with self.assertRaisesMessage(ValidationError, "'Enter a list of values.'"):
            f.clean("hello")
        with self.assertRaisesMessage(ValidationError, "'This field is required.'"):
            f.clean([])
        with self.assertRaisesMessage(ValidationError, "'This field is required.'"):
            f.clean(())
        msg = "'Select a valid choice. 3 is not one of the available choices.'"
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean(["3"])