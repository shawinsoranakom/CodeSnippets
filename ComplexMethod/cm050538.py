def _message_post_after_hook(self, message, msg_vals):
        if message.attachment_ids and not self.displayed_image_id:
            image_attachments = message.attachment_ids.filtered(lambda a: a.mimetype == 'image')
            if image_attachments:
                self.displayed_image_id = image_attachments[0]

        # use the sanitized body of the email from the message thread to populate the task's description
        if (
           not self.description
           and message.subtype_id == self._creation_subtype()
           and self.partner_id == message.author_id
           and msg_vals['message_type'] == 'email'
           and msg_vals.get('body')
        ):
            # Remove the signature from the email body
            source_html = msg_vals.get('body')
            doc = html.fromstring(source_html)

            signature_xpath = (
                '//*[@id="Signature"] | '
                '//*[@data-smartmail="gmail_signature"] | '
                '//span[normalize-space(.) = "--"]'
            )

            for element in doc.xpath(signature_xpath):
                element.getparent().remove(element)

            cleaned_html = html.tostring(doc, encoding='unicode').strip()
            self.description = html_sanitize(cleaned_html)

        return super()._message_post_after_hook(message, msg_vals)