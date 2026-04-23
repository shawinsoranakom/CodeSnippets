def _import_ubl_invoice_line_add_allowance_charges_values(self, collected_values):
        line_tree = collected_values['line_tree']
        allowances = collected_values['allowances'] = []
        charges = collected_values['charges'] = []
        for allowance_charge_elem in line_tree.iterfind('./{*}AllowanceCharge'):
            charge_indicator = allowance_charge_elem.findtext('.//{*}ChargeIndicator')
            amount_str = allowance_charge_elem.findtext('.//{*}Amount')
            base_amount_str = allowance_charge_elem.findtext('.//{*}BaseAmount')
            reason = allowance_charge_elem.findtext('.//{*}AllowanceChargeReason')
            reason_code = allowance_charge_elem.findtext('.//{*}AllowanceChargeReasonCode')

            if amount_str:
                amount = float(amount_str)
            else:
                continue

            allowance_charge_values = {
                'amount': amount,
                'base_amount': float(base_amount_str) if base_amount_str else None,
                'reason': reason,
                'reason_code': reason_code,
            }
            if charge_indicator.lower() == 'true':
                charges.append(allowance_charge_values)
            else:
                allowances.append(allowance_charge_values)

        allowance_elem = line_tree.find('./{*}Price/{*}AllowanceCharge')
        collected_values['price_allowance_values'] = {}
        if allowance_elem is not None:
            charge_indicator = allowance_elem.findtext('./{*}ChargeIndicator') or 'false'
            amount_str = allowance_elem.findtext('./{*}Amount')
            base_amount_str = allowance_elem.findtext('./{*}BaseAmount')
            reason = allowance_elem.findtext('./{*}AllowanceChargeReason')
            reason_code = allowance_elem.findtext('./{*}AllowanceChargeReasonCode')

            if charge_indicator.lower() == 'true':
                charge_indicator_sign = 1
            else:
                charge_indicator_sign = -1

            collected_values['price_allowance_values'] = {
                'charge_indicator_sign': charge_indicator_sign,
                'amount': float(amount_str) if amount_str else None,
                'base_amount': float(base_amount_str) if base_amount_str else None,
                'reason': reason,
                'reason_code': reason_code,
            }