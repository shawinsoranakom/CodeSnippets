def test_safedata(self):
        """
        A message containing SafeData is keeping its safe status when
        retrieved from the message storage.
        """
        self.assertIsInstance(
            self.encode_decode(mark_safe("<b>Hello Django!</b>")).message,
            SafeData,
        )
        self.assertNotIsInstance(
            self.encode_decode("<b>Hello Django!</b>").message,
            SafeData,
        )