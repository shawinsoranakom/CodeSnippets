def write(self, vals):
        if not vals:
            return True
        protected_fields = self._get_lock_date_protected_fields()
        account_to_write = self.env['account.account'].browse(vals['account_id']) if 'account_id' in vals else None

        # Check writing a archived account.
        if account_to_write and not account_to_write.active:
            raise UserError(_('You cannot use an archived account.'))

        inalterable_fields = set(self._get_integrity_hash_fields()).union({'inalterable_hash'})
        hashed_moves = self.move_id.filtered('inalterable_hash')
        violated_fields = set(vals) & inalterable_fields
        if hashed_moves and violated_fields:
            raise UserError(_(
                "You cannot edit the following fields: %(fields)s.\n"
                "The following entries are already hashed:\n%(entries)s",
                fields=[f['string'] for f in self.fields_get(violated_fields).values()],
                entries='\n'.join(hashed_moves.mapped('name')),
            ))

        line_to_write = self
        vals = self._sanitize_vals(vals)
        matching2lines = None  # lazy cache
        lines_to_unreconcile = self.env['account.move.line']
        st_lines_to_unreconcile = self.env['account.bank.statement.line']
        tax_lock_check_ids = []
        for line in self:
            if not any(self.env['account.move']._field_will_change(line, vals, field_name) for field_name in vals):
                line_to_write -= line
                continue

            if line.parent_state == 'posted' and any(self.env['account.move']._field_will_change(line, vals, field_name) for field_name in ('tax_ids', 'tax_line_id')):
                raise UserError(_('You cannot modify the taxes related to a posted journal item, you should reset the journal entry to draft to do so.'))

            # Check the lock date.
            if line.parent_state == 'posted' and any(self.env['account.move']._field_will_change(line, vals, field_name) for field_name in protected_fields['fiscal']):
                line.move_id._check_fiscal_lock_dates()

            # Check the tax lock date.
            if line.parent_state == 'posted' and any(self.env['account.move']._field_will_change(line, vals, field_name) for field_name in protected_fields['tax']):
                tax_lock_check_ids.append(line.id)

            # Break the reconciliation.
            if (
                line.matching_number
                and (changing_fields := {
                    field_name
                    for field_name in protected_fields['reconciliation']
                    if self.env['account.move']._field_will_change(line, vals, field_name)
                })
            ):
                matching2lines = self._reconciled_by_number() if matching2lines is None else matching2lines
                if (
                    # allow changing the account on all the lines of a reconciliation together
                    changing_fields - {'account_id'}
                    or not all(reconciled_line in self for reconciled_line in matching2lines[line.matching_number])
                ):
                    lines_to_unreconcile += line
                    st_lines_to_unreconcile += (line.matched_debit_ids.debit_move_id + line.matched_credit_ids.credit_move_id).statement_line_id

        lines_to_unreconcile.remove_move_reconcile()
        for st_line in st_lines_to_unreconcile:
            try:
                st_line.move_id._check_fiscal_lock_dates()
                st_line.move_id.line_ids._check_tax_lock_date()
            except UserError:
                st_lines_to_unreconcile -= st_line
        st_lines_to_unreconcile.action_undo_reconciliation()

        self.browse(tax_lock_check_ids)._check_tax_lock_date()

        move_container = {'records': self.move_id}
        with self.move_id._check_balanced(move_container),\
             self.env.protecting(self.env['account.move']._get_protected_vals(vals, self)),\
             self.move_id._sync_dynamic_lines(move_container),\
             self._sync_invoice({'records': self}):
            self = line_to_write
            if not self:
                return True
            # Tracking stuff can be skipped for perfs using tracking_disable context key
            if not self.env.context.get('tracking_disable', False):
                # Get all tracked fields (without related fields because these fields must be manage on their own model)
                tracking_fields = []
                for value in vals:
                    field = self._fields[value]
                    if hasattr(field, 'related') and field.related:
                        continue # We don't want to track related field.
                    if hasattr(field, 'tracking') and field.tracking:
                        tracking_fields.append(value)
                ref_fields = self.env['account.move.line'].fields_get(tracking_fields)

                # Get initial values for each line
                move_initial_values = {}
                for line in self.filtered(lambda l: l.move_id.posted_before): # Only lines with posted once move.
                    for field in tracking_fields:
                        # Group initial values by move_id
                        if line.move_id.id not in move_initial_values:
                            move_initial_values[line.move_id.id] = {}
                        move_initial_values[line.move_id.id].update({field: line[field]})

            result = super().write(vals)
            self.move_id._synchronize_business_models(['line_ids'])
            if any(field in vals for field in ['account_id', 'currency_id']):
                self._check_constrains_account_id_journal_id()

            # double check modified lines in case a tax field was changed on a line that didn't previously affect tax
            self.browse(tax_lock_check_ids)._check_tax_lock_date()

            if not self.env.context.get('tracking_disable', False):
                # Log changes to move lines on each move
                for move_id, modified_lines in move_initial_values.items():
                    for line in self.filtered(lambda l: l.move_id.id == move_id):
                        tracking_value_ids = line._mail_track(ref_fields, modified_lines)[1]
                        if tracking_value_ids:
                            msg = _("Journal Item %s updated", line._get_html_link(title=f"#{line.id}"))
                            line.move_id._message_log(
                                body=msg,
                                tracking_value_ids=tracking_value_ids
                            )
            if 'analytic_line_ids' in vals:
                self.filtered(lambda l: l.parent_state == 'draft').analytic_line_ids.with_context(skip_analytic_sync=True).unlink()

        return result