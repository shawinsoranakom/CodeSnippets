def l10n_gr_edi_try_send_expense_classification(self):
        moves_to_send = self.env['account.move']
        for move in self:
            if error_message := move._l10n_gr_edi_get_pre_error_string():
                move._l10n_gr_edi_create_error_document({'error': error_message})

                # Simulate the error handling behavior on invoice's send and print wizard.
                # If we're only sending one bill, raise the warning error immediately.
                if len(self) == 1 and self._can_commit():
                    self.env.cr.commit()
                    raise UserError(error_message)
            else:
                moves_to_send |= move

        if moves_to_send:
            moves_to_send._l10n_gr_edi_send_expense_classification()
            if len(self) == 1 and (error_message := self.l10n_gr_edi_document_ids.sorted()[0].message):
                raise UserError(error_message)