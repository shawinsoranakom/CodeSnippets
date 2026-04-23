def _import_ubl_invoice_add_allowances_charges_values(self, collected_values):
        tree = collected_values['tree']
        odoo_document_type = collected_values['odoo_document_type']
        allowances = collected_values['allowances'] = []
        charges = collected_values['charges'] = []
        taxes_values = collected_values['taxes_values'] = []

        for element in tree.iterfind('./{*}AllowanceCharge'):
            reason = element.findtext('./{*}AllowanceChargeReason')
            reason_code = element.findtext('./{*}AllowanceChargeReasonCode')
            charge_indicator = element.findtext('./{*}ChargeIndicator')
            amount_str = element.findtext('./{*}Amount')
            base_amount_str = element.findtext('./{*}BaseAmount')
            multiplier_factor_numeric_str = element.findtext('./{*}MultiplierFactorNumeric')
            percentage_str = element.findtext('./{*}TaxCategory/{*}Percent')
            category_code = element.findtext('./{*}TaxCategory/{*}ID')

            if amount_str:
                amount = float(amount_str)
            else:
                amount = 0.0

            if not percentage_str:
                continue

            percentage = float(percentage_str)
            allowance_charge_values = {
                'amount': amount,
                'base_amount': float(base_amount_str) if base_amount_str else None,
                'reason': reason,
                'reason_code': reason_code,
                'multiplier_factor_numeric': float(multiplier_factor_numeric_str) if multiplier_factor_numeric_str else None,
                'tax_percentage': percentage,
                'charge_indicator': charge_indicator,
            }
            if charge_indicator.lower() == 'true':
                charges.append(allowance_charge_values)
            else:
                allowances.append(allowance_charge_values)

            # Try to link the allowance / charge with a percentage tax.
            if not category_code:
                continue

            allowance_charge_values['attempt_tax_values'] = tax_values = {
                'amount_type': 'percent',
                'type_tax_use': odoo_document_type,
                'ubl_cii_tax_category_code': category_code,
                'amount': percentage,
            }
            taxes_values.append(tax_values)