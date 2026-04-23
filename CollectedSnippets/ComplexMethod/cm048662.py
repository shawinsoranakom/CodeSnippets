def write(self, vals):
        if not vals:
            return True
        self._sanitize_vals(vals)

        for move in self:
            if vals.get('checked') and not move._is_user_able_to_review():
                raise AccessError(_("You don't have the access rights to perform this action."))
            if vals.get('state') == 'draft' and move.checked and not move._is_user_able_to_review():
                raise ValidationError(_("Validated entries can only be changed by your accountant."))

            violated_fields = set(vals).intersection(move._get_integrity_hash_fields() + ['inalterable_hash'])
            if move.inalterable_hash and violated_fields:
                raise UserError(_(
                    "This document is protected by a hash. "
                    "Therefore, you cannot edit the following fields: %s.",
                    ', '.join(f['string'] for f in self.fields_get(violated_fields).values())
                ))
            if (
                    move.posted_before
                    and 'journal_id' in vals and move.journal_id.id != vals['journal_id']
                    and not (move.name == '/' or not move.name or ('name' in vals and (vals['name'] == '/' or not vals['name'])))
            ):
                raise UserError(_('You cannot edit the journal of an account move if it has been posted once, unless the name is removed or set to "/". This might create a gap in the sequence.'))
            if (
                    move.name and move.name != '/'
                    and move.sequence_number not in (0, 1)
                    and 'journal_id' in vals and move.journal_id.id != vals['journal_id']
                    and not move.quick_edit_mode
                    and not ('name' in vals and (vals['name'] == '/' or not vals['name']))
            ):
                raise UserError(_('You cannot edit the journal of an account move with a sequence number assigned, unless the name is removed or set to "/". This might create a gap in the sequence.'))

            # You can't change the date or name of a move being inside a locked period.
            if move.state == "posted" and (
                    ('name' in vals and move.name != vals['name'])
                    or ('date' in vals and move.date != vals['date'])
            ):
                move._check_fiscal_lock_dates()
                move.line_ids._check_tax_lock_date()

            # You can't post subtract a move to a locked period.
            if 'state' in vals and move.state == 'posted' and vals['state'] != 'posted':
                move._check_fiscal_lock_dates()
                move.line_ids._check_tax_lock_date()

            # Disallow modifying readonly fields on a posted move
            move_state = vals.get('state', move.state)
            unmodifiable_fields = (
                'invoice_line_ids', 'line_ids', 'invoice_date', 'date', 'partner_id',
                'invoice_payment_term_id', 'currency_id', 'fiscal_position_id', 'invoice_cash_rounding_id')
            readonly_fields = [val for val in vals if val in unmodifiable_fields]
            if not self.env.context.get('skip_readonly_check') and move_state == "posted" and readonly_fields:
                raise UserError(_("You cannot modify the following readonly fields on a posted move: %s", ', '.join(readonly_fields)))

            if move.journal_id.sequence_override_regex and vals.get('name') and vals['name'] != '/' and not re.match(move.journal_id.sequence_override_regex, vals['name']):
                if not self.env.user.has_group('account.group_account_manager'):
                    raise UserError(_('The Journal Entry sequence is not conform to the current format. Only the Accountant can change it.'))
                move.journal_id.sequence_override_regex = False

        if {'sequence_prefix', 'sequence_number', 'journal_id', 'name'} & vals.keys():
            self._set_next_made_sequence_gap(True)

        stolen_moves = self.browse(set(move for move in self._stolen_move(vals)))
        container = {'records': self | stolen_moves}
        with self.env.protecting(self._get_protected_vals(vals, self)), self._check_balanced(container):
            with self._sync_dynamic_lines(container):
                if 'is_manually_modified' not in vals and not self.env.context.get('skip_is_manually_modified'):
                    vals['is_manually_modified'] = True

                res = super(AccountMove, self.with_context(
                    skip_account_move_synchronization=True,
                )).write(vals)

                # Reset the name of draft moves when changing the journal.
                # Protected against holes in the pre-validation checks.
                if 'journal_id' in vals and 'name' not in vals:
                    draft_move = self.filtered(lambda m: not m.posted_before)
                    draft_move.name = False
                    draft_move._compute_name()

                # You can't change the date of a not-locked move to a locked period.
                # You can't post a new journal entry inside a locked period.
                if 'date' in vals or 'state' in vals:
                    posted_move = self.filtered(lambda m: m.state == 'posted')
                    posted_move._check_fiscal_lock_dates()
                    posted_move.line_ids._check_tax_lock_date()

                if vals.get('state') == 'posted':
                    self.flush_recordset()  # Ensure that the name is correctly computed
                    self._hash_moves()

            self._synchronize_business_models(set(vals.keys()))

            # Apply the rounding on the Quick Edit mode only when adding a new line
            for move in self:
                if 'tax_totals' in vals:
                    super(AccountMove, move).write({'tax_totals': vals['tax_totals']})

        if any(field in vals for field in ['journal_id', 'currency_id']):
            self.line_ids._check_constrains_account_id_journal_id()

        return res