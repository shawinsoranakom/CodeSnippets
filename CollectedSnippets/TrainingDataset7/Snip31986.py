def test_save(self):
        msg = self.not_implemented_msg % "a save"
        with self.assertRaisesMessage(NotImplementedError, msg):
            self.session.save()