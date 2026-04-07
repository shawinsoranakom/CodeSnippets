def test_validate_property(self):
        class TestUser(models.Model):
            pass

            @property
            def username(self):
                return "foobar"

        msg = "The password is too similar to the username."
        with self.assertRaisesMessage(ValidationError, msg):
            UserAttributeSimilarityValidator().validate("foobar", user=TestUser())