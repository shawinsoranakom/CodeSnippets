def test_bool_unsupported(self):
        msg = "type 'bool' is not an acceptable base type"
        with self.assertRaisesMessage(TypeError, msg):

            class Boolean(bool, models.Choices):
                pass