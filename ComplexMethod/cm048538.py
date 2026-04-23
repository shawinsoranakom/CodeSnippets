def portal_my_journal_unsubscribe(self, journal_id, **kw):
        def _render(ctx, status=200):
            return request.render('account.portal_my_journal_mail_notifications', ctx, status=status)

        if access_token := kw.get('token'):
            try:
                token_data = verify_hash_signed(request.env(su=True), request.env['account.journal']._get_journal_notification_unsubscribe_scope(), access_token)
            except ValueError:
                return _render({'error': _('Invalid token')}, 403)
            if not token_data or token_data.get('journal_id') != journal_id:
                return _render({'error': _('Invalid token')}, 403)
            journal = request.env['account.journal'].sudo().browse(journal_id)
        else:
            # Legacy link for authenticated user trying to unsubscribe (needs access rights on journal)
            journal = request.env['account.journal'].browse(journal_id)

        if access_token:
            email_to_unsubscribe = email_normalize(token_data.get('email_to_unsubscribe'), strict=False)
        else:
            emails = email_normalize_all(journal.incoming_einvoice_notification_email or '')
            if len(emails) != 1:
                return _render({'error': _('Deprecated link')}, 410)
            email_to_unsubscribe = emails[0]

        if not journal.exists() or not email_to_unsubscribe:
            return _render({'error': _('Already unsubscribed')}, 404)

        if not journal.has_access('write'):
            return _render({'error': _('Invalid token')}, 403)

        journal = journal.with_company(journal.sudo().company_id.id)

        all_recipients = email_normalize_all(journal.incoming_einvoice_notification_email or '')
        email_found = any(r == email_to_unsubscribe for r in all_recipients)

        if not email_found:
            return _render({'error': _('Already unsubscribed')}, 404)

        if request.httprequest.method == 'POST':
            journal._unsubscribe_invoice_notification_email(email_to_unsubscribe)
            return _render({'journal': journal, 'email': email_to_unsubscribe, 'completed': True})

        return _render({'journal': journal, 'email': email_to_unsubscribe})