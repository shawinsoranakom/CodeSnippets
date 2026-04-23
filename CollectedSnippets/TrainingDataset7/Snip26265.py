def test_rejects_non_ascii_local_part(self):
        """
        The SMTP EmailBackend does not currently support non-ASCII local-parts.
        (That would require using the RFC 6532 SMTPUTF8 extension.) #35713.
        """
        backend = smtp.EmailBackend()
        backend.connection = mock.Mock(spec=object())
        email = EmailMessage(to=["nø@example.dk"])
        with self.assertRaisesMessage(
            ValueError,
            "Invalid address 'nø@example.dk': local-part contains non-ASCII characters",
        ):
            backend.send_messages([email])