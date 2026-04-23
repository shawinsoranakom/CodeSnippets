def _send(self, auto_commit=False, raise_exception=False, smtp_session=None, alias_domain_id=False,
              mail_server=False, post_send_callback=None):
        IrMailServer = self.env['ir.mail_server']
        if IrMailServer._disable_send():
            # during testing skip sending e-mails unless monkeypatched
            return True
        # check that every email is allowed on this mail server
        if mail_server and not self._filter_mail_mail_servers(mail_server):
            raise UserError(_('Unauthorized server for some of the sending mails.'))
        # Only retrieve recipient followers of the mails if needed
        mails_with_unfollow_link = self.filtered(lambda m: m.body_html and '/mail/unfollow' in m.body_html)
        doc_to_followers = self.env['mail.followers']._get_mail_doc_to_followers(mails_with_unfollow_link.ids)

        for mail_id in self.ids:
            success_pids = []
            success_emails = []
            failure_reason = None
            failure_type = None
            mail = None
            try:
                mail = self.browse(mail_id)
                if mail.state != 'outgoing':
                    continue
                no_recipients = (not (mail.email_to or '').strip() and not mail.recipient_ids and not (mail.email_cc or '').strip())

                # Writing on the mail object may fail (e.g. lock on user) which
                # would trigger a rollback *after* actually sending the email.
                # To avoid sending twice the same email, provoke the failure earlier
                mail.write({
                    'state': 'exception',
                    'failure_reason': IrMailServer.NO_VALID_RECIPIENT if no_recipients else _('Error without exception. Probably due to sending an email without computed recipients.'),
                    'failure_type': 'mail_email_missing' if no_recipients else 'unknown',
                })
                # Update notification in a transient exception state to avoid concurrent
                # update in case an email bounces while sending all emails related to current
                # mail record.
                notifs = self.env['mail.notification'].search([
                    ('notification_type', '=', 'email'),
                    ('mail_mail_id', 'in', mail.ids),
                    ('notification_status', 'not in', ('sent', 'canceled'))
                ])
                if notifs:
                    notif_msg = _('Error without exception. Probably due to concurrent access update of notification records. Please see with an administrator.')
                    notifs.sudo().write({
                        'notification_status': 'exception',
                        'failure_type': 'unknown',
                        'failure_reason': notif_msg,
                    })
                    # `test_mail_bounce_during_send`, force immediate update to obtain the lock.
                    # see rev. 56596e5240ef920df14d99087451ce6f06ac6d36
                    notifs.flush_recordset(['notification_status', 'failure_type', 'failure_reason'])

                # protect against ill-formatted email_from when formataddr was used on an already formatted email
                emails_from = tools.mail.email_split_and_format_normalize(mail.email_from)
                email_from = emails_from[0] if emails_from else mail.email_from

                # build an RFC2822 email.message.Message object and send it without queuing
                res = None
                # TDE note: could be great to pre-detect missing to/cc and skip sending it
                # to go directly to failed state update
                email_list = mail._prepare_outgoing_list(
                    mail_server=mail_server or mail.mail_server_id,
                    doc_to_followers=doc_to_followers,
                )

                # send each sub-email
                for email in email_list:
                    # give indication to 'send_mail' about emails already considered
                    # as being valid
                    email_to_normalized = email.pop('email_to_normalized', [])
                    # if given, contextualize sending using alias domains
                    if alias_domain_id:
                        alias_domain = self.env['mail.alias.domain'].sudo().browse(alias_domain_id)
                        SendIrMailServer = IrMailServer.with_context(
                            domain_notifications_email=alias_domain.default_from_email,
                            domain_bounce_address=email['headers'].get('Return-Path') or alias_domain.bounce_email,
                            send_validated_to=email_to_normalized,
                        )
                    else:
                        SendIrMailServer = IrMailServer.with_context(send_validated_to=email_to_normalized)
                    msg = SendIrMailServer._build_email__(
                        email_from=email_from,
                        email_to=email['email_to'],
                        subject=email['subject'],
                        body=email['body'],
                        body_alternative=email['body_alternative'],
                        email_cc=email['email_cc'],
                        reply_to=email['reply_to'],
                        attachments=email['attachments'],
                        message_id=email['message_id'],
                        references=email['references'],
                        object_id=email['object_id'],
                        subtype='html',
                        subtype_alternative='plain',
                        headers=email['headers'],
                    )
                    processing_pid = email.pop("partner_id", None)
                    try:
                        res = SendIrMailServer.send_email(
                            msg, mail_server_id=mail.mail_server_id.id, smtp_session=smtp_session)
                        if processing_pid:
                            success_pids.append(processing_pid)
                        else:
                            success_emails.extend(email['email_to'] or [])
                        processing_pid = None
                    except AssertionError as error:
                        if str(error) == IrMailServer.NO_VALID_RECIPIENT:
                            # if we have a list of void emails for email_list -> email missing, otherwise generic email failure
                            if not email.get('email_to') and failure_type != "mail_email_invalid":
                                failure_type = "mail_email_missing"
                            else:
                                failure_type = "mail_email_invalid"
                            failure_reason = tools.exception_to_unicode(error)
                            # No valid recipient found for this particular
                            # mail item -> ignore error to avoid blocking
                            # delivery to next recipients, if any. If this is
                            # the only recipient, the mail will show as failed.
                            _logger.info("Ignoring invalid recipients for mail.mail %s: %s",
                                         mail.message_id, email.get('email_to'))
                        else:
                            raise
                if res:  # mail has been sent at least once, no major exception occurred
                    mail.write({'state': 'sent', 'message_id': res, 'failure_type': False, 'failure_reason': False})
                    if not modules.module.current_test:
                        _logger.info(
                            "Mail (mail.mail) with ID %r and Message-Id %r from %r to (redacted) %s successfully sent",
                            mail.id,
                            mail.message_id,
                            tools.email_normalize(msg['from']),  # FROM should not change, so last msg good enough
                            ', '.join(
                                repr(tools.mail.email_anonymize(tools.email_normalize(m['email_to'])))
                                for m in email_list
                            ),
                        )
                        _logger.info("Total emails tried by SMTP: %s", len(email_list))

                    # /!\ can't use mail.state here, as mail.refresh() will cause an error
                    # see revid:odo@openerp.com-20120622152536-42b2s28lvdv3odyr in 6.1
                else:
                    mail_vals = {}
                    if failure_reason:
                        mail_vals['failure_reason'] = failure_reason
                    if failure_type:
                        mail_vals['failure_type'] = failure_type
                    if mail_vals:
                        mail.write(mail_vals)
                mail._postprocess_sent_message(success_pids=success_pids, success_emails=success_emails, failure_type=failure_type, failure_reason=failure_reason)
            except MemoryError:
                # prevent catching transient MemoryErrors, bubble up to notify user or abort cron job
                # instead of marking the mail as failed
                _logger.exception(
                    'MemoryError while processing mail with ID %r and Msg-Id %r. Consider raising the --limit-memory-hard startup option',
                    mail.id, mail.message_id)
                # mail status will stay on ongoing since transaction will be rollback
                raise
            except (psycopg2.Error, smtplib.SMTPServerDisconnected):
                # If an error with the database or SMTP session occurs, chances are that the cursor
                # or SMTP session are unusable, causing further errors when trying to save the state.
                _logger.exception(
                    'Exception while processing mail with ID %r and Msg-Id %r.',
                    mail.id, mail.message_id)
                raise
            except Exception as e:
                if isinstance(e, AssertionError):
                    # Handle assert raised in IrMailServer to try to catch notably from-specific errors.
                    # Note that assert may raise several args, a generic error string then a specific
                    # message for logging in failure type
                    error_code = e.args[0]
                    if len(e.args) > 1 and error_code == IrMailServer.NO_VALID_FROM:
                        # log failing email in additional arguments message
                        failure_reason = str(e.args[1])
                    else:
                        failure_reason = error_code
                    if error_code == IrMailServer.NO_VALID_FROM:
                        failure_type = "mail_from_invalid"
                    elif error_code in (IrMailServer.NO_FOUND_FROM, IrMailServer.NO_FOUND_SMTP_FROM):
                        failure_type = "mail_from_missing"

                if isinstance(e, MailDeliveryException) and "OutboundSpamException" in str(e):
                    # OutboundSpamException: Outlook spam error
                    failure_type = "mail_spam"

                # generic (unknown) error as fallback
                if not failure_reason:
                    failure_reason = tools.exception_to_unicode(e)
                if not failure_type:
                    failure_type = "unknown"

                _logger.exception('failed sending mail (id: %s) due to %s', mail.id, failure_reason)
                mail.write({
                    "failure_reason": failure_reason,
                    "failure_type": failure_type,
                    "state": "exception",
                })
                mail._postprocess_sent_message(
                    success_pids=success_pids, success_emails=success_emails,
                    failure_reason=failure_reason, failure_type=failure_type
                )
                if raise_exception:
                    if isinstance(e, (AssertionError, UnicodeEncodeError)):
                        if isinstance(e, UnicodeEncodeError):
                            value = "Invalid text: %s" % e.object
                        else:
                            value = '. '.join(e.args)
                        raise MailDeliveryException(value)
                    raise
            if auto_commit is True:
                if post_send_callback:
                    post_send_callback([mail_id])
                self.env.cr.commit()
        if post_send_callback:
            post_send_callback(self.ids)
        return True