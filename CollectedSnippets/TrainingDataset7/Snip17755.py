def test_user_creation_form_class_getitem(self):
        self.assertIs(BaseUserCreationForm["MyCustomUser"], BaseUserCreationForm)