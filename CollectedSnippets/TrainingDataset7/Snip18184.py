def test_str(self):
        p = Permission.objects.get(codename="view_customemailfield")
        self.assertEqual(
            str(p), "Auth_Tests | custom email field | Can view custom email field"
        )