def _message_parse_extract_payload(self, message: EmailMessage, message_dict: dict, save_original: bool = False):
        """Extract body as HTML and attachments from the mail message
        """
        attachments = []
        body = ''
        if save_original:
            attachments.append(self._Attachment('original_email.eml', message.as_string(), {}))

        # Be careful, content-type may contain tricky content like in the
        # following example so test the MIME type with startswith()
        #
        # Content-Type: multipart/related;
        #   boundary="_004_3f1e4da175f349248b8d43cdeb9866f1AMSPR06MB343eurprd06pro_";
        #   type="text/html"
        if message.get_content_maintype() == 'text':
            body = message.get_content()
            if message.get_content_type() == 'text/plain':
                # text/plain -> <pre/>
                body = append_content_to_html('', body, preserve=True)
            elif message.get_content_type() == 'text/html':
                # we only strip_classes here everything else will be done in by html field of mail.message
                body = html_sanitize(body, sanitize_tags=False, strip_classes=True)
        else:
            alternative = False
            mixed = False
            html = False
            for part in message.walk():
                if message_dict.get('is_bounce') and body:
                    # bounce email, keep only the first body and ignore
                    # the parent email that might be added at the end
                    # (e.g. for outlook / yahoo bounce email)
                    break
                if (bad_content_type := part.get_content_type()) in BAD_CONTENT_TYPES:
                    _logger.warning("Message containing an unexpected Content-Type %r, assuming 'application/octet-stream'", bad_content_type)
                    part.replace_header('Content-Type', 'application/octet-stream')
                if part.get_content_type() == 'multipart/alternative':
                    alternative = True
                if part.get_content_type() == 'multipart/mixed':
                    mixed = True
                if part.get_content_maintype() == 'multipart':
                    continue  # skip container

                filename = part.get_filename()  # I may not properly handle all charsets
                if part.get_content_type().startswith('text/') and not part.get_param('charset'):
                    # for text/* with omitted charset, the charset is assumed to be ASCII by the `email` module
                    # although the payload might be in UTF8
                    part.set_charset('utf-8')
                encoding = part.get_content_charset()  # None if attachment

                # Correcting MIME type for PDF files
                if part.get('Content-Type', '').startswith('pdf;'):
                    part.replace_header('Content-Type', 'application/pdf' + part.get('Content-Type', '')[3:])

                content = part.get_content()
                info = {'encoding': encoding}
                # 0) Inline Attachments -> attachments, with a third part in the tuple to match cid / attachment
                if filename and part.get('content-id'):
                    info['cid'] = part.get('content-id').strip('><')
                    attachments.append(self._Attachment(filename, content, info))
                    continue
                # 1) Explicit Attachments -> attachments
                if filename or part.get('content-disposition', '').strip().startswith('attachment'):
                    attachments.append(self._Attachment(filename or 'attachment', content, info))
                    continue
                # 2) text/plain -> <pre/>
                if part.get_content_type() == 'text/plain' and not (alternative and body):
                    body = append_content_to_html(body, content, preserve=True)
                # 3) text/html -> raw
                elif part.get_content_type() == 'text/html':
                    # multipart/alternative have one text and a html part, keep only the second
                    if alternative and not (html and mixed):
                        body = content
                    else:
                        # mixed allows several html parts, append html content
                        body = append_content_to_html(body, content, plaintext=False)
                    # TODO: maybe just setting to `True` is enough?
                    html = html or bool(content)
                    # we only strip_classes here everything else will be done in by html field of mail.message
                    body = html_sanitize(body, sanitize_tags=False, strip_classes=True)
                # 4) Anything else -> attachment
                else:
                    attachments.append(self._Attachment(filename or 'attachment', content, info))

        return self._message_parse_extract_payload_postprocess(message, {'body': body, 'attachments': attachments})