def message(self, *, policy=email.policy.default):
        msg = email.message.EmailMessage(policy=policy)
        self._add_bodies(msg)
        self._add_attachments(msg)

        msg["Subject"] = str(self.subject)
        msg["From"] = str(self.extra_headers.get("From", self.from_email))
        self._set_list_header_if_not_empty(msg, "To", self.to)
        self._set_list_header_if_not_empty(msg, "Cc", self.cc)
        self._set_list_header_if_not_empty(msg, "Reply-To", self.reply_to)

        # Email header names are case-insensitive (RFC 2045), so we have to
        # accommodate that when doing comparisons.
        header_names = [key.lower() for key in self.extra_headers]
        if "date" not in header_names:
            if settings.EMAIL_USE_LOCALTIME:
                tz = get_current_timezone()
            else:
                tz = timezone.utc
            msg["Date"] = datetime.now(tz)
        if "message-id" not in header_names:
            # Use cached DNS_NAME for performance
            msg["Message-ID"] = make_msgid(domain=DNS_NAME)
        for name, value in self.extra_headers.items():
            # Avoid headers handled above.
            if name.lower() not in {"from", "to", "cc", "reply-to"}:
                msg[name] = force_str(value, strings_only=True)
        self._idna_encode_address_header_domains(msg)
        return msg