def test_CharField(self):
        self.assertFormfield(Member, "name", widgets.AdminTextInputWidget)