def test_null_characters_prohibited(self):
        f = CharField()
        msg = "Null characters are not allowed."
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean("\x00something")