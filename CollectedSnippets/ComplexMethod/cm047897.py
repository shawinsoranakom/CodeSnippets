def _l10n_ke_validate_move(self):
        """ Returns list of errors related to misconfigurations per move

        Find misconfigurations on the move, the lines of the move, and the
        taxes on those lines that would result in rejection by the KRA.
        """
        errors = []
        for move in self:
            move_errors = []
            if move.country_code != 'KE':
                move_errors.append(_("This invoice is not a Kenyan invoice and therefore can not be sent to the device."))

            if move.company_id.currency_id != self.env.ref('base.KES'):
                move_errors.append(_("This invoice's company currency is not in Kenyan Shillings, conversion to KES is not possible."))

            if move.state != 'posted':
                move_errors.append(_("This invoice/credit note has not been posted. Please confirm it to continue."))

            if move.move_type not in ('out_refund', 'out_invoice'):
                move_errors.append(_("The document being sent should be an invoice or credit note."))

            if any([move.l10n_ke_cu_invoice_number, move.l10n_ke_cu_serial_number, move.l10n_ke_cu_qrcode, move.l10n_ke_cu_datetime]):
                move_errors.append(_("The document already has details related to the fiscal device. Please make sure that the invoice has not already been sent."))

            # The credit note should refer to the control unit number (receipt number) of the original
            # invoice to which it relates.
            if move.move_type == 'out_refund' and not move.reversed_entry_id.l10n_ke_cu_invoice_number:
                move_errors.append(_("This credit note must reference the previous invoice, and this previous invoice must have already been submitted."))

            for line in self.invoice_line_ids.filtered(lambda l: l.display_type == 'product'):
                vat_taxes = line.tax_ids.filtered(lambda tax: tax.amount in (16, 8, 0))
                if not vat_taxes or len(vat_taxes) > 1:
                    move_errors.append(_("On line %s, you must select one and only one VAT tax.", line.name))
                else:
                    if vat_taxes[0].amount == 0 and not line.tax_ids[0].l10n_ke_item_code_id:
                        move_errors.append(_("On line %s, a tax with a KRA item code must be selected, since the tax is 0%% or exempt.", line.name))

            if move_errors:
                errors.append((move.name, move_errors))

        return errors