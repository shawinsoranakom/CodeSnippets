def write(self, vals):
        # EXTENDS base res.partner.bank
        # Track and log changes to partner_id, heavily inspired from account_move
        account_initial_values = defaultdict(dict)
        # Get all tracked fields (without related fields because these fields must be managed on their own model)
        tracking_fields = []
        for field_name in vals:
            field = self._fields[field_name]
            if not (hasattr(field, 'related') and field.related) and hasattr(field, 'tracking') and field.tracking:
                tracking_fields.append(field_name)
        fields_definition = self.env['res.partner.bank'].fields_get(tracking_fields)

        # Get initial values for each account
        for account in self:
            for field in tracking_fields:
                # Group initial values by partner_id
                account_initial_values[account][field] = account[field]

        # Some fields should not be editable based on conditions. It is enforced in the view, but not in python which
        # leaves them vulnerable to edits via the shell/... So we need to ensure that the user has the rights to edit
        # these fields when writing too.
        # While we do lock changes if the account is trusted, we still want to allow to change them if we go from not trusted -> trusted or from trusted -> not trusted.
        trusted_accounts = self.filtered(lambda x: x.lock_trust_fields)
        if not trusted_accounts:
            should_allow_changes = True  # If we were on a non-trusted account, we will allow to change (setting/... one last time before trusting)
        else:
            # If we were on a trusted account, we only allow changes if the account is moving to untrusted.
            should_allow_changes = self.env.su or ('allow_out_payment' in vals and vals['allow_out_payment'] is False)

        lock_fields = {'acc_number', 'sanitized_acc_number', 'partner_id', 'acc_type'}
        if not should_allow_changes and any(
            account[fname] != account._fields[fname].convert_to_record(
                account._fields[fname].convert_to_cache(vals[fname], account),
                account,
            )
            for fname in lock_fields & set(vals)
            for account in trusted_accounts
        ):
            raise UserError(_("You cannot modify the account number or partner of an account that has been trusted."))

        if 'allow_out_payment' in vals and any(not bank._user_can_trust() for bank in self):
            raise UserError(_("You do not have the rights to trust or un-trust accounts."))

        res = super().write(vals)

        # Check
        if "allow_out_payment" in vals:
            self._check_allow_out_payment()

        # Log changes to move lines on each move
        for account, initial_values in account_initial_values.items():
            tracking_value_ids = account._mail_track(fields_definition, initial_values)[1]
            if tracking_value_ids:
                msg = _("Bank Account %s updated", account._get_html_link(title=f"#{account.id}"))
                account.partner_id._message_log(body=msg, tracking_value_ids=tracking_value_ids)
                if 'partner_id' in initial_values:  # notify previous partner as well
                    initial_values['partner_id']._message_log(body=msg, tracking_value_ids=tracking_value_ids)
        return res