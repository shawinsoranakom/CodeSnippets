def test_multipart_encoded_form(self):
        class FormWithoutFile(Form):
            username = CharField()

        class FormWithFile(Form):
            username = CharField()
            file = FileField()

        class FormWithImage(Form):
            image = ImageField()

        self.assertFalse(FormWithoutFile().is_multipart())
        self.assertTrue(FormWithFile().is_multipart())
        self.assertTrue(FormWithImage().is_multipart())