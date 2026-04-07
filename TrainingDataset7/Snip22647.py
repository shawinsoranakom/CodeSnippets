def test_bad_choice(self):
        msg = "'Select a valid choice. X is not one of the available choices.'"
        with self.assertRaisesMessage(ValidationError, msg):
            self.field.clean(["some text", ["X"], ["2007-04-25", "6:24:00"]])