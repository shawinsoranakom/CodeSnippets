async def handle_DATA(self, server, session, envelope):
        data = envelope.content
        mail_from = envelope.mail_from

        # Convert SMTP's CRNL to NL, to simplify content checks in shared test
        # cases.
        message = message_from_bytes(data.replace(b"\r\n", b"\n"))
        try:
            header_from = message["from"].addresses[0].addr_spec
        except (KeyError, IndexError):
            header_from = None

        if mail_from != header_from:
            return f"553 '{mail_from}' != '{header_from}'"
        self.mailbox.append(message)
        self.smtp_envelopes.append(
            {
                "mail_from": envelope.mail_from,
                "rcpt_tos": envelope.rcpt_tos,
            }
        )
        return "250 OK"