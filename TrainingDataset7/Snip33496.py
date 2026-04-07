def test_cycle01(self):
        msg = "No named cycles in template. 'a' is not defined"
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            self.engine.get_template("cycle01")