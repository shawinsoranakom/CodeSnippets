def test_model(self):
        r1 = Redirect.objects.create(
            site=self.site, old_path="/initial", new_path="/new_target"
        )
        self.assertEqual(str(r1), "/initial ---> /new_target")