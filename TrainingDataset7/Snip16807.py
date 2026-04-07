def test_EmailField(self):
        self.assertFormfield(Member, "email", widgets.AdminEmailInputWidget)