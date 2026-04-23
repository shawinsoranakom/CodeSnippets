def _check_move_constraints(self, moves):
        # HR-BR-37: Invoice must contain HR-BT-4: Operator code in accordance with the Fiscalization Act.
        if any((move.country_code == 'HR' and not move.l10n_hr_operator_name) for move in moves):
            raise UserError(self.env._("Operator label is required for sending invoices in Croatia."))
        # HR-BR-9: Invoice must contain HR-BT-5: Operator OIB in accordance with the Fiscalization Act.
        if any((move.country_code == 'HR' and not move.l10n_hr_operator_oib) for move in moves):
            raise UserError(self.env._("Operator OIB is required for sending invoices in Croatia."))
        # HR-BR-25: ensure KPD is provided for every business line except for advance (P4)
        if any((move.country_code == 'HR' and move.l10n_hr_process_type != 'P4' and
                any(line.display_type == 'product' and not line.l10n_hr_kpd_category_id for line in move.line_ids)) for move in moves):
            raise UserError(self.env._('KPD categories must be defined on every invoice line for any Business Process Type other than P4.'))
        if any((move.country_code == 'HR' and move.l10n_hr_process_type == 'P99' and not move.l10n_hr_customer_defined_process_name) for move in moves):
            raise UserError(self.env._('Name of custom business process is required for Business Process Type P99.'))
        if any((move.country_code == 'HR' and
                len({line.tax_ids.tax_exigibility for line in move.line_ids if line.display_type == 'product'}) != 1) for move in moves):
            raise ValidationError(self.env._('For Croatia, all VAT taxes on an invoice should either be cash basis or not.'))
        if any(move.country_code == 'HR' and
            any(any((tax.tax_exigibility == 'on_payment' and not tax.invoice_legal_notes) for tax in line.tax_ids
             ) for line in move.line_ids if line.display_type == 'product') for move in moves):
            raise ValidationError(self.env._('For Croatia, Legal Notes should be provided for all cash basis taxes.'))
        super()._check_move_constraints(moves)