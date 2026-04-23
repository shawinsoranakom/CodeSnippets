def test_message(self):
        msg = "This backend does not support explaining query execution."
        with self.assertRaisesMessage(NotSupportedError, msg):
            Tag.objects.filter(name="test").explain()