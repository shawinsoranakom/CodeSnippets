def test_save_doesnt_clear_data(self):
        self.session["a"] = "b"
        self.session.save()
        self.assertEqual(self.session["a"], "b")