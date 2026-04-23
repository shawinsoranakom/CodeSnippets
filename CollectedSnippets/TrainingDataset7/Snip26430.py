def test_custom_max_lengths(self):
        args = {
            "email": "someone@example.com",
            "vcard": "vcard",
            "homepage": "http://example.com/",
            "avatar": "me.jpg",
        }

        for field in ("email", "vcard", "homepage", "avatar"):
            new_args = args.copy()
            new_args[field] = (
                "X" * 250
            )  # a value longer than any of the default fields could hold.
            p = PersonWithCustomMaxLengths.objects.create(**new_args)
            self.assertEqual(getattr(p, field), ("X" * 250))