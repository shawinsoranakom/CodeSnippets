def test_cycle07(self):
        msg = "Could not parse the remainder: ',b,c' from 'a,b,c'"
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            self.engine.get_template("cycle07")