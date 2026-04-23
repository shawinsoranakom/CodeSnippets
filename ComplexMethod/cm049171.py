def l10n_tr_check_nilvera_customer(self):
        results = defaultdict(lambda: self.env['res.partner'])
        # we want to skip records whose status is already set, unless we want to
        # purposefully retry them
        retry_existing = self.env.context.get('retry_existing', False)
        for record in self.filtered(lambda p: p.vat and (retry_existing or p.l10n_tr_nilvera_customer_status == 'not_checked')):
            if record._check_nilvera_customer():
                if len(record.l10n_tr_nilvera_customer_alias_ids) > 1:
                    results['multi_alias'] |= record
                else:
                    results['success'] |= record
            else:
                results['failure'] |= record

        if results['failure']:
            self._send_user_notification('danger', _('Nilvera verification failed. Please try again.'))
        if results['success']:
            self._send_user_notification('success', _('Nilvera status verified successfully.'))
        if multi_alias := results['multi_alias']:
            self._send_user_notification(
                'warning',
                _('Multiple alias entries were found for the following partners. Please verify the correct one manually.'),
                action_button={
                    'name': _('View Partners'),
                    'action_name': _('Partners in Error'),
                    'model': 'res.partner',
                    'res_ids': multi_alias.ids,
                },
            )