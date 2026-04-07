def test_validate(self):
        user = User.objects.create_user(
            username="testclient",
            password="password",
            email="testclient@example.com",
            first_name="Test",
            last_name="Client",
        )
        expected_error = "The password is too similar to the %s."

        self.assertIsNone(UserAttributeSimilarityValidator().validate("testclient"))

        with self.assertRaises(ValidationError) as cm:
            UserAttributeSimilarityValidator().validate("testclient", user=user)
        self.assertEqual(cm.exception.messages, [expected_error % "username"])
        self.assertEqual(cm.exception.error_list[0].code, "password_too_similar")

        msg = expected_error % "email address"
        with self.assertRaisesMessage(ValidationError, msg):
            UserAttributeSimilarityValidator().validate("example.com", user=user)

        msg = expected_error % "first name"
        with self.assertRaisesMessage(ValidationError, msg):
            UserAttributeSimilarityValidator(
                user_attributes=["first_name"],
                max_similarity=0.3,
            ).validate("testclient", user=user)
        # max_similarity=1 doesn't allow passwords that are identical to the
        # attribute's value.
        msg = expected_error % "first name"
        with self.assertRaisesMessage(ValidationError, msg):
            UserAttributeSimilarityValidator(
                user_attributes=["first_name"],
                max_similarity=1,
            ).validate(user.first_name, user=user)
        # Very low max_similarity is rejected.
        msg = "max_similarity must be at least 0.1"
        with self.assertRaisesMessage(ValueError, msg):
            UserAttributeSimilarityValidator(max_similarity=0.09)
        # Passes validation.
        self.assertIsNone(
            UserAttributeSimilarityValidator(user_attributes=["first_name"]).validate(
                "testclient", user=user
            )
        )