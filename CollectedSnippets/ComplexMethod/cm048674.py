def _get_move_display_name(self, show_ref=False):
        ''' Helper to get the display name of an invoice depending of its type.
        :param show_ref:    A flag indicating of the display name must include or not the journal entry reference.
        :return:            A string representing the invoice.
        '''
        self.ensure_one()
        if self.env.context.get('name_as_amount_total'):
            currency_amount = self.currency_id.format(self.amount_total)
            if self.is_sale_document(include_receipts=True) and self.state == "posted":
                ref = f" - {self.ref}" if self.ref else ""
                return _("%(name)s%(ref)s at %(currency_amount)s", name=(self.name), ref=ref, currency_amount=currency_amount)
            label = (self.ref or self.name or "") if self.is_purchase_document(include_receipts=True) else (self.name or "")
            if label:
                if self.state == 'draft':
                    return _("%(label)s at %(currency_amount)s (Draft)", label=label, currency_amount=currency_amount)
                return _("%(label)s at %(currency_amount)s", label=label, currency_amount=currency_amount)
            return _("Draft (%(currency_amount)s)", currency_amount=currency_amount)

        name = ''
        if self.state == 'draft':
            name += {
                'out_invoice': _('Draft Invoice'),
                'out_refund': _('Draft Credit Note'),
                'in_invoice': _('Draft Bill'),
                'in_refund': _('Draft Vendor Credit Note'),
                'out_receipt': _('Draft Sales Receipt'),
                'in_receipt': _('Draft Purchase Receipt'),
                'entry': _('Draft Entry'),
            }[self.move_type]
        if self.name and self.name != '/':
            name = f"{name} {self.name}".strip()
            if self.env.context.get('input_full_display_name'):
                if self.partner_id:
                    name += f', {self.partner_id.name}'
                if self.date:
                    name += f', {format_date(self.env, self.date)}'
        return name + (f" ({shorten(self.ref, width=50)})" if show_ref and self.ref else '')