def test_choicefield_3(self):
        f = ChoiceField(choices=[("J", "John"), ("P", "Paul")])
        self.assertEqual("J", f.clean("J"))
        msg = "'Select a valid choice. John is not one of the available choices.'"
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean("John")