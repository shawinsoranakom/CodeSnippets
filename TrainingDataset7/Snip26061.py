def test_undocumented_alternative_subtype(self):
        """
        Trying to use the previously undocumented, now unsupported
        EmailMultiAlternatives.alternative_subtype causes an error.
        """
        msg = (
            "EmailMultiAlternatives no longer supports"
            " the undocumented `alternative_subtype` attribute"
        )
        email = EmailMultiAlternatives(
            alternatives=[EmailAlternative("", "text/plain")]
        )
        email.alternative_subtype = "multilingual"
        with self.assertRaisesMessage(AttributeError, msg):
            email.message()