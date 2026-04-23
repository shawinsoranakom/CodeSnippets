def _message_update_content(self, message, /, *, body, attachment_ids=None, partner_ids=None,
                                strict=True, **kwargs):
        """ Update message content. Currently does not support attachments
        specific code (see ``_process_attachments_for_post``), to be added
        when necessary.

        Private method to use for tooling, do not expose to interface as editing
        messages should be avoided at all costs (think of: notifications already
        sent, ...).

        :param <mail.message> message: message to update, should be linked to self through
          model and res_id;
        :param str body: new body (None to skip its update);
        :param list attachment_ids: list of new attachments IDs, replacing old one (None
          to skip its update);
        :param list attachment_ids: list of new partner IDs that are mentioned;
        :param bool strict: whether to check for allowance before updating
          content. This should be skipped only when really necessary as it
          creates issues with already-sent notifications, lack of content
          tracking, ...

        Kwargs are supported, notably to match mail.message fields to update.
        See content of this method for more details about supported keys.
        """
        self.ensure_one()
        if strict:
            self._check_can_update_message_content(message.sudo())

        msg_values = {}
        if body is not None:
            if body or not message._filter_empty():
                tree = html.fragment_fromstring(escape(body), create_parent="div")
                children = tree.getchildren()
                if len(children) > 0:  # body is a valid html
                    # If the last element is a div or p, add the edited span inside it to avoid the edit markup
                    # to be on its own line. Otherwise, append it to the end of the last element.
                    last_div_element = (
                        children[-1] if children[-1].tag in ["div", "p"] else tree
                    )
                    last_div_element.text = (last_div_element.text or '') + (' ' if last_div_element.text else '')
                    etree.SubElement(last_div_element, "span", attrib={"class": "o-mail-Message-edited"})
                    msg_values["body"] = (
                        # markup: it is considered safe, as coming from html.fragment_fromstring
                        (tree.text or "") + Markup("".join(etree.tostring(child, encoding="unicode") for child in tree))
                    )
                else:  # body is plain text
                    # keep html if already Markup, otherwise escape
                    msg_values["body"] = escape(body) + Markup("<span class='o-mail-Message-edited'/>")
            else:
                msg_values["body"] = ""
        if attachment_ids:
            msg_values.update(
                self._process_attachments_for_post([], attachment_ids, {
                    'body': body,
                    'model': self._name,
                    'res_id': self.id,
                })
            )
        elif attachment_ids is not None:  # None means "no update"
            message.attachment_ids._delete_and_notify()
        if partner_ids is not None:
            msg_values.update({"partner_ids": [int(pid) for pid in partner_ids] or False})
        if msg_values:
            message.write(msg_values)
        if message._filter_empty():
            self._clean_empty_message(message)

        if 'scheduled_date' in kwargs:
            # update scheduled datetime
            if kwargs['scheduled_date']:
                self.env['mail.message.schedule'].sudo()._update_message_scheduled_datetime(
                    message,
                    kwargs['scheduled_date']
                )
            # (re)send notifications
            else:
                self.env['mail.message.schedule'].sudo()._send_message_notifications(message)

        res = [
            Store.Many("attachment_ids", sort="id"),
            "body",
            Store.Many("partner_ids", ["avatar_128", "name"]),
            "pinned_at",
            "write_date",
            *message._get_store_linked_messages_fields(),
            *self._get_store_message_update_extra_fields(),
        ]
        if body is not None:
            # sudo: mail.message.translation - discarding translations of message after editing it
            self.env["mail.message.translation"].sudo().search([("message_id", "=", message.id)]).unlink()
            res.append({"translationValue": False})
        Store(bus_channel=message._bus_channel()).add(message, res).bus_send()