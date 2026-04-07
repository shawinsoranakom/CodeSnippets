def set_payload(self, payload, charset=None):
        if charset == "utf-8" and not isinstance(charset, Charset.Charset):
            has_long_lines = any(
                len(line.encode(errors="surrogateescape"))
                > RFC5322_EMAIL_LINE_LENGTH_LIMIT
                for line in payload.splitlines()
            )
            # Quoted-Printable encoding has the side effect of shortening long
            # lines, if any (#22561).
            charset = utf8_charset_qp if has_long_lines else utf8_charset
        MIMEText.set_payload(self, payload, charset=charset)