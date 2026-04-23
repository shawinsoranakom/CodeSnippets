def send(
        self,
        to: str | list[str],
        subject: str,
        body: str,
        cc: str | list[str] | None = None,
        attachs: Sequence[tuple[str, str, IO[Any]]] = (),
        mimetype: str = "text/plain",
        charset: str | None = None,
        _callback: Callable[..., None] | None = None,
    ) -> Deferred[None] | None:
        from twisted.internet import reactor

        msg: MIMEBase = (
            MIMEMultipart() if attachs else MIMENonMultipart(*mimetype.split("/", 1))
        )

        to = list(arg_to_iter(to))
        cc = list(arg_to_iter(cc))

        msg["From"] = self.mailfrom
        msg["To"] = COMMASPACE.join(to)
        msg["Date"] = formatdate(localtime=True)
        msg["Subject"] = subject
        rcpts = to[:]
        if cc:
            rcpts.extend(cc)
            msg["Cc"] = COMMASPACE.join(cc)

        if attachs:
            if charset:
                msg.set_charset(charset)
            msg.attach(MIMEText(body, "plain", charset or "us-ascii"))
            for attach_name, attach_mimetype, f in attachs:
                part = MIMEBase(*attach_mimetype.split("/"))
                part.set_payload(f.read())
                Encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition", "attachment", filename=attach_name
                )
                msg.attach(part)
        else:
            msg.set_payload(body, charset)

        if _callback:
            _callback(to=to, subject=subject, body=body, cc=cc, attach=attachs, msg=msg)

        if self.debug:
            logger.debug(
                "Debug mail sent OK: To=%(mailto)s Cc=%(mailcc)s "
                'Subject="%(mailsubject)s" Attachs=%(mailattachs)d',
                {
                    "mailto": to,
                    "mailcc": cc,
                    "mailsubject": subject,
                    "mailattachs": len(attachs),
                },
            )
            return None

        dfd: Deferred[Any] = self._sendmail(
            rcpts, msg.as_string().encode(charset or "utf-8")
        )
        dfd.addCallback(self._sent_ok, to, cc, subject, len(attachs))
        dfd.addErrback(self._sent_failed, to, cc, subject, len(attachs))
        reactor.addSystemEventTrigger("before", "shutdown", lambda: dfd)
        return dfd