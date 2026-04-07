def test_DateTimeField(self):
        self.assertFormfield(Member, "birthdate", widgets.AdminSplitDateTime)