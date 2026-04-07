def test_message_policy_cte_7bit(self):
        """
        Allows a policy that requires 7bit encodings.
        """
        email = EmailMessage(body="Detta innehåller icke-ASCII-tecken")
        email.attach("file.txt", "يحتوي هذا المرفق على أحرف غير ASCII")

        # Uses 8bit by default. (Test pre-condition.)
        self.assertIn(b"Content-Transfer-Encoding: 8bit", email.message().as_bytes())

        # Uses something 7bit compatible when policy requires it. Should pick
        # the shorter of quoted-printable (for this body) or base64 (for this
        # attachment), but must not use 8bit. (Decoding to "ascii" verifies
        # that.)
        policy_7bit = policy.default.clone(cte_type="7bit")
        msg_bytes = email.message(policy=policy_7bit).as_bytes()
        msg_ascii = msg_bytes.decode("ascii")
        self.assertIn("Content-Transfer-Encoding: quoted-printable", msg_ascii)
        self.assertIn("Content-Transfer-Encoding: base64", msg_ascii)
        self.assertNotIn("Content-Transfer-Encoding: 8bit", msg_ascii)