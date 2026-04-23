def test_illegal_kwargs_message(self):
        msg = (
            "Reverse for 'places' with keyword arguments '{'arg1': 2}' not found. 1 "
            "pattern(s) tried:"
        )
        with self.assertRaisesMessage(NoReverseMatch, msg):
            reverse("places", kwargs={"arg1": 2})