def test_message_policy_compat32(self):
        """
        Although EmailMessage.message() doesn't support policy=compat32
        (because compat32 doesn't support modern APIs), compat32 _can_ be
        used with as_bytes() or as_string() on the resulting message.
        """
        # This subject results in different (but equivalent) RFC 2047 encoding
        # with compat32 vs. email.policy.default.
        email = EmailMessage(subject="Detta ämne innehåller icke-ASCII-tecken")
        message = email.message()
        self.assertIn(
            b"Subject: =?utf-8?q?Detta_=C3=A4mne_inneh=C3=A5ller_icke-ASCII-tecken?=\n",
            message.as_bytes(policy=policy.compat32),
        )
        self.assertIn(
            "Subject: =?utf-8?q?Detta_=C3=A4mne_inneh=C3=A5ller_icke-ASCII-tecken?=\n",
            message.as_string(policy=policy.compat32),
        )