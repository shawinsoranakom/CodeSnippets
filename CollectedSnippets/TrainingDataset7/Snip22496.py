def test_choicefield_4(self):
        f = ChoiceField(
            choices=[
                ("Numbers", (("1", "One"), ("2", "Two"))),
                ("Letters", (("3", "A"), ("4", "B"))),
                ("5", "Other"),
            ]
        )
        self.assertEqual("1", f.clean(1))
        self.assertEqual("1", f.clean("1"))
        self.assertEqual("3", f.clean(3))
        self.assertEqual("3", f.clean("3"))
        self.assertEqual("5", f.clean(5))
        self.assertEqual("5", f.clean("5"))
        msg = "'Select a valid choice. 6 is not one of the available choices.'"
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean("6")