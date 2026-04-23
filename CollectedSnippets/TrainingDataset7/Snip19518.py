def test_invalid_level(self):
        msg = "The first argument should be level."
        with self.assertRaisesMessage(TypeError, msg):
            CheckMessage("ERROR", "Message")