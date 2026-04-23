def send(self, auto_commit=False, raise_exception=False, post_send_callback=None):
        """ Sends the selected emails immediately, ignoring their current
            state (mails that have already been sent should not be passed
            unless they should actually be re-sent).
            Emails successfully delivered are marked as 'sent', and those
            that fail to be deliver are marked as 'exception', and the
            corresponding error mail is output in the server logs.

            :param bool auto_commit: whether to force a commit of the mail status
                after sending each mail (meant only for scheduler processing);
                should never be True during normal transactions (default: False)
            :param bool raise_exception: whether to raise an exception if the
                email sending process has failed
            :param post_send_callback: an optional function, called as ``post_send_callback(ids, force=False)``,
                with the mail ids that have been sent; calls with redundant ids
                are possible
            :return: True
        """
        for mail_server_id, alias_domain_id, smtp_from, batch_ids in self._split_by_mail_configuration():
            mail_server = self.env["ir.mail_server"].browse(mail_server_id)

            if mail_server and mail_server.owner_user_id:
                # Throttle the sending that use personal mail servers
                batch_ids = self.browse(batch_ids)._split_by_delayed_batch(mail_server).ids
                if not batch_ids:
                    continue

            smtp_session = None
            try:
                smtp_session = self.env['ir.mail_server']._connect__(mail_server_id=mail_server_id, smtp_from=smtp_from)
            except Exception as exc:
                if raise_exception:
                    # To be consistent and backward compatible with mail_mail.send() raised
                    # exceptions, it is encapsulated into an Odoo MailDeliveryException
                    raise MailDeliveryException(_('Unable to connect to SMTP Server'), exc)
                else:
                    batch = self.browse(batch_ids)
                    batch.write({'state': 'exception', 'failure_reason': tools.exception_to_unicode(exc)})
                    batch._postprocess_sent_message(success_pids=[], success_emails=[], failure_type="mail_smtp")
            else:
                self.browse(batch_ids)._send(
                    auto_commit=auto_commit,
                    raise_exception=raise_exception,
                    smtp_session=smtp_session,
                    alias_domain_id=alias_domain_id,
                    mail_server=mail_server,
                    post_send_callback=post_send_callback,
                )
                if not modules.module.current_test:
                    _logger.info(
                        "Processed batch of %s mail.mail records via mail server ID #%s",
                        len(batch_ids), mail_server_id)
            finally:
                if smtp_session:
                    try:
                        smtp_session.quit()
                    except smtplib.SMTPServerDisconnected:
                        _logger.info(
                            "Ignoring SMTPServerDisconnected while trying to quit non open session"
                        )