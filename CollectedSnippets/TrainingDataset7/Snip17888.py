def assertMakePasswordCalled(self, password, encoded, hasher_side_effect):
        hasher = get_hasher("default")
        with (
            mock.patch(
                "django.contrib.auth.hashers.identify_hasher",
                side_effect=hasher_side_effect,
            ) as mock_identify_hasher,
            mock.patch(
                "django.contrib.auth.hashers.make_password"
            ) as mock_make_password,
            mock.patch(
                "django.contrib.auth.hashers.get_random_string",
                side_effect=lambda size: "x" * size,
            ),
            mock.patch.object(hasher, "verify"),
        ):
            # Ensure make_password is called to standardize timing.
            yield
            self.assertEqual(hasher.verify.call_count, 0)
            self.assertEqual(mock_identify_hasher.mock_calls, [mock.call(encoded)])
            self.assertEqual(
                mock_make_password.mock_calls,
                [mock.call("x" * UNUSABLE_PASSWORD_SUFFIX_LENGTH)],
            )