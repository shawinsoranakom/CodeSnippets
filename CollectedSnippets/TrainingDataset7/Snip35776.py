def test_no_args_message(self):
        msg = "Reverse for 'places' with no arguments not found. 1 pattern(s) tried:"
        with self.assertRaisesMessage(NoReverseMatch, msg):
            reverse("places")