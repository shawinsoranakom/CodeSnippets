def test_illegal_args_message(self):
        msg = (
            "Reverse for 'places' with arguments '(1, 2)' not found. 1 pattern(s) "
            "tried:"
        )
        with self.assertRaisesMessage(NoReverseMatch, msg):
            reverse("places", args=(1, 2))