def test_load(self):
        msg = self.not_implemented_msg % "a load"
        with self.assertRaisesMessage(NotImplementedError, msg):
            self.session.load()