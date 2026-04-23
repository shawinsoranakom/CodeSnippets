def _compute_l10n_gr_edi_inv_type(self):
        for move in self:
            if move.country_code == 'GR':
                if move.l10n_gr_edi_inv_type or move.move_type == 'entry':
                    # If we have previously calculated the inv_type, reuse it here.
                    # For entry moves, we want the inv_type to be False. (we don't send anything to myDATA on entry moves)
                    move.l10n_gr_edi_inv_type = move.l10n_gr_edi_inv_type
                elif move.move_type in ('out_refund', 'in_refund'):
                    # inv_type specific for credit notes
                    if move.l10n_gr_edi_correlation_id:
                        # when possible, we must add the associate invoice/bill mark (id)
                        move.l10n_gr_edi_inv_type = '5.1'
                    else:
                        move.l10n_gr_edi_inv_type = '5.2'
                else:  # move.move_type in ('out_invoice', 'in_invoice', 'out_receipt', 'in_receipt')
                    inv_type = '1.1' if move.move_type == 'out_invoice' else '13.1'
                    preferred_clss = move.fiscal_position_id.l10n_gr_edi_preferred_classification_ids.filtered(
                        lambda p: p.l10n_gr_edi_inv_type in (move.l10n_gr_edi_available_inv_type or "").split(','))
                    if preferred_clss:
                        inv_type = preferred_clss[0].l10n_gr_edi_inv_type
                    move.l10n_gr_edi_inv_type = inv_type
            else:
                move.l10n_gr_edi_inv_type = False