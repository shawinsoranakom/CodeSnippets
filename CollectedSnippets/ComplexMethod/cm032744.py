def _email(self, name, blob, **kwargs):
        """Parse eml/msg files into structured email content."""
        self.callback(random.randint(1, 5) / 100.0, "Start to work on an email.")

        email_content = {}
        conf = self._param.setups["email"]
        self.set_output("output_format", conf["output_format"])
        target_fields = conf["fields"]

        _, ext = os.path.splitext(name)
        if ext == ".eml":
            # handle eml file
            from email import policy
            from email.parser import BytesParser

            msg = BytesParser(policy=policy.default).parse(io.BytesIO(blob))
            email_content["metadata"] = {}
            # handle header info
            for header, value in msg.items():
                # get fields like from, to, cc, bcc, date, subject
                if header.lower() in target_fields:
                    email_content[header.lower()] = value
                # get metadata
                elif header.lower() not in ["from", "to", "cc", "bcc", "date", "subject"]:
                    email_content["metadata"][header.lower()] = value
            # get body
            if "body" in target_fields:
                body_text, body_html = [], []

                def _add_content(m, content_type):
                    def _decode_payload(payload, charset, target_list):
                        try:
                            target_list.append(payload.decode(charset))
                        except (UnicodeDecodeError, LookupError):
                            for enc in ["utf-8", "gb2312", "gbk", "gb18030", "latin1"]:
                                try:
                                    target_list.append(payload.decode(enc))
                                    break
                                except UnicodeDecodeError:
                                    continue
                            else:
                                target_list.append(payload.decode("utf-8", errors="ignore"))

                    if content_type == "text/plain":
                        payload = msg.get_payload(decode=True)
                        charset = msg.get_content_charset() or "utf-8"
                        _decode_payload(payload, charset, body_text)
                    elif content_type == "text/html":
                        payload = msg.get_payload(decode=True)
                        charset = msg.get_content_charset() or "utf-8"
                        _decode_payload(payload, charset, body_html)
                    elif "multipart" in content_type:
                        if m.is_multipart():
                            for part in m.iter_parts():
                                _add_content(part, part.get_content_type())

                _add_content(msg, msg.get_content_type())

                email_content["text"] = "\n".join(body_text)
                email_content["text_html"] = "\n".join(body_html)
            # get attachment
            if "attachments" in target_fields:
                attachments = []
                for part in msg.iter_attachments():
                    content_disposition = part.get("Content-Disposition")
                    if content_disposition:
                        dispositions = content_disposition.strip().split(";")
                        if dispositions[0].lower() == "attachment":
                            filename = part.get_filename()
                            payload = part.get_payload(decode=True).decode(part.get_content_charset())
                            attachments.append(
                                {
                                    "filename": filename,
                                    "payload": payload,
                                }
                            )
                email_content["attachments"] = attachments
        else:
            # handle msg file
            import extract_msg

            msg = extract_msg.Message(blob)
            # handle header info
            basic_content = {
                "from": msg.sender,
                "to": msg.to,
                "cc": msg.cc,
                "bcc": msg.bcc,
                "date": msg.date,
                "subject": msg.subject,
            }
            email_content.update({k: v for k, v in basic_content.items() if k in target_fields})
            # get metadata
            email_content["metadata"] = {
                "message_id": msg.messageId,
                "in_reply_to": msg.inReplyTo,
            }
            # get body
            if "body" in target_fields:
                email_content["text"] = msg.body[0] if isinstance(msg.body, list) and msg.body else msg.body
                if not email_content["text"] and msg.htmlBody:
                    email_content["text"] = msg.htmlBody[0] if isinstance(msg.htmlBody, list) and msg.htmlBody else msg.htmlBody
            # get attachments
            if "attachments" in target_fields:
                attachments = []
                for t in msg.attachments:
                    attachments.append(
                        {
                            "filename": t.name,
                            "payload": t.data.decode("utf-8"),
                        }
                    )
                email_content["attachments"] = attachments

        if conf["output_format"] == "json":
            email_content["doc_type_kwd"] = "text"
            self.set_output("json", [email_content])
        else:
            content_txt = ""
            for k, v in email_content.items():
                if isinstance(v, str):
                    # basic info
                    content_txt += f"{k}:{v}" + "\n"
                elif isinstance(v, dict):
                    # metadata
                    content_txt += f"{k}:{json.dumps(v)}" + "\n"
                elif isinstance(v, list):
                    # attachments or others
                    for fb in v:
                        if isinstance(fb, dict):
                            # attachments
                            content_txt += f"{fb['filename']}:{fb['payload']}" + "\n"
                        else:
                            # str, usually plain text
                            content_txt += fb
            self.set_output("text", content_txt)