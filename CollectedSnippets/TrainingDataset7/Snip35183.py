def test_reset_sequences(self):
        old_reset_sequences = self.__class__.reset_sequences
        self.__class__.reset_sequences = True
        self.addCleanup(setattr, self.__class__, "reset_sequences", old_reset_sequences)
        msg = "reset_sequences cannot be used on TestCase instances"
        with self.assertRaisesMessage(TypeError, msg):
            self._fixture_setup()