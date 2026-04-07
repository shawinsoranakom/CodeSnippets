def test_undocumented_mixed_subtype(self):
        """
        Trying to use the previously undocumented, now unsupported
        EmailMessage.mixed_subtype causes an error.
        """
        msg = (
            "EmailMessage no longer supports"
            " the undocumented `mixed_subtype` attribute"
        )
        email = EmailMessage(
            attachments=[EmailAttachment(None, b"GIF89a...", "image/gif")]
        )
        email.mixed_subtype = "related"
        with self.assertRaisesMessage(AttributeError, msg):
            email.message()