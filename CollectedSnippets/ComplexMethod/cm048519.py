def _compute_qr_code(self):
        for pay in self:
            qr_html = False
            if pay.partner_bank_id \
               and pay.partner_bank_id.allow_out_payment \
               and pay.payment_method_line_id.code == 'manual' \
               and pay.payment_type == 'outbound' \
               and pay.amount \
               and pay.currency_id:
                b64_qr = pay.partner_bank_id.build_qr_code_base64(
                    amount=pay.amount,
                    free_communication=pay.communication,
                    structured_communication=pay.communication,
                    currency=pay.currency_id,
                    debtor_partner=pay.partner_id,
                )
                if b64_qr:
                    qr_html = f'''
                        <img class="border border-dark rounded" src="{b64_qr}"/>
                        <br/>
                        <strong>{_('Scan me with your banking app.')}</strong>
                    '''
            pay.qr_code = qr_html