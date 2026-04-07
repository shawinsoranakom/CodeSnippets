def test_abstract_model_not_instantiated(self):
        msg = "Abstract models cannot be instantiated."
        with self.assertRaisesMessage(TypeError, msg):
            AbstractPerson()