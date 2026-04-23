def _check_lines(self):
        error_message = []
        invoice_lines = self.account_move_id.invoice_line_ids
        AccountMove = self.env['account.move']
        if not any(l.product_id for l in invoice_lines):
            error_message.append(_("Ensure that at least one line item includes a product."))
            return error_message
        if all(
            AccountMove._l10n_in_is_service_hsn(l.l10n_in_hsn_code)
            for l in invoice_lines if l.product_id
        ):
            error_message.append(_("You need at least one product having 'Product Type' as stockable or consumable."))
            return error_message
        for line in invoice_lines:
            if (
                line.display_type == 'product'
                and not AccountMove._l10n_in_is_service_hsn(line.l10n_in_hsn_code)
                and (hsn_error_message := line._l10n_in_check_invalid_hsn_code())
            ):
                error_message.append(hsn_error_message)
        return error_message