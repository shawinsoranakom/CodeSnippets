def _ubl_add_legal_monetary_total_allowance_charge_total_amount_node(self, vals, in_foreign_currency=True):
        currency = vals['currency_id'] if in_foreign_currency else vals['company_currency']
        node = vals['legal_monetary_total_node']

        total_allowance = sum(
            allowance_node['cbc:Amount']['_text']
                for allowance_node in vals['document_node']['cac:AllowanceCharge']
                if allowance_node['cbc:ChargeIndicator']['_text'] != 'false'
        )
        total_charge = sum(
            charge_node['cbc:Amount']['_text']
                for charge_node in vals['document_node']['cac:AllowanceCharge']
                if charge_node['cbc:ChargeIndicator']['_text'] != 'true'
        )

        node.update({
            'cbc:AllowanceTotalAmount': {
                '_text': FloatFmt(total_allowance, max_dp=currency.decimal_places),
                'currencyID': currency.name,
            } if total_allowance else None,
            'cbc:ChargeTotalAmount': {
                '_text': FloatFmt(total_charge, max_dp=currency.decimal_places),
                'currencyID': currency.name,
            } if total_charge else None,
        })