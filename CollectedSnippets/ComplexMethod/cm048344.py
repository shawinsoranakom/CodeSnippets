def rating_apply(self, rate, token=None, rating=None, feedback=None,
                     subtype_xmlid=None, notify_delay_send=False):
        """ Apply a rating to the record. This rating can either be linked to a
        token (customer flow) or directly a rating record (code flow).

        If the current model inherits from mail.thread mixin a message is posted
        on its chatter. User going through this method should have at least
        employee rights as well as rights on the current record because of rating
        manipulation and chatter post (either employee, either sudo-ed in public
        controllers after security check granting access).

        :param float rate: the rating value to apply (from 0 to 5);
        :param string token: access token to fetch the rating to apply (optional);
        :param record rating: rating.rating to apply (if no token);
        :param string feedback: additional feedback (plaintext);
        :param string subtype_xmlid: xml id of a valid mail.message.subtype used
          to post the message (if it applies). If not given a classic comment is
          posted;
        :param notify_delay_send: Delay the sending by 2 hours of the email so the user
            can still change his feedback. If False, the email will be sent immediately.

        :returns: rating.rating record
        """
        if rate < 0 or rate > 5:
            raise ValueError(_('Wrong rating value. A rate should be between 0 and 5 (received %d).', rate))
        if token:
            rating = self.env['rating.rating'].search([('access_token', '=', token)], limit=1)
        if not rating:
            raise ValueError(_('Invalid token or rating.'))

        rating.write({'rating': rate, 'feedback': feedback, 'consumed': True})
        if isinstance(self, self.env.registry['mail.thread']):
            if subtype_xmlid is None:
                subtype_id = self._rating_apply_get_default_subtype_id()
            else:
                subtype_id = False
            feedback = tools.plaintext2html(feedback or '', with_paragraph=False)

            scheduled_datetime = (
                fields.Datetime.now() + datetime.timedelta(hours=2)
                if notify_delay_send else None
            )
            rating_body = (
                    markupsafe.Markup(
                        "<img src='%s' alt=':%s/5' style='width:18px;height:18px;float:left;margin-right: 5px;'/>%s"
                    ) % (rating.rating_image_url, rate, feedback)
            )

            if rating.message_id:
                self._message_update_content(
                    rating.message_id,
                    body=rating_body,
                    scheduled_date=scheduled_datetime,
                    strict=False,
                )
            else:
                self.message_post(
                    author_id=rating.partner_id.id or None,  # None will set the default author in mail/mail_thread.py
                    body=rating_body,
                    rating_id=rating.id,
                    scheduled_date=scheduled_datetime,
                    subtype_id=subtype_id,
                    subtype_xmlid=subtype_xmlid,
                )
        return rating